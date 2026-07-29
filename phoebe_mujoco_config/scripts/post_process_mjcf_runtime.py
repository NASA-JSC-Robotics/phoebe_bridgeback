#!/usr/bin/env python3
#
# Copyright (c) 2026, United States Government, as represented by the
# Administrator of the National Aeronautics and Space Administration.
#
# All rights reserved.
#
# This software is licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import argparse
import os
import shutil
import subprocess
import sys
from xml.dom import minidom

import rclpy
from ament_index_python.packages import get_package_share_directory
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import (
    QoSDurabilityPolicy,
    QoSHistoryPolicy,
    QoSProfile,
    QoSReliabilityPolicy,
)
from std_msgs.msg import String


class StringModifierNode(Node):
    def __init__(
        self,
        tf_prefix="",
        magic_carpet=False,
        wheels_package="phoebe_mujoco_config",
        left_gripper="hande",
        right_gripper="hande",
        copy_assets=False,
    ):
        super().__init__("string_modifier_node")

        self.tf_prefix = tf_prefix
        self.magic_carpet = magic_carpet
        self.wheels_package = wheels_package
        self.left_gripper = left_gripper
        self.right_gripper = right_gripper
        self.copy_assets = copy_assets

        # Set up robot description publisher/subscriber with the same QoS.
        qos_profile = QoSProfile(depth=1)
        qos_profile.reliability = QoSReliabilityPolicy.RELIABLE
        qos_profile.durability = QoSDurabilityPolicy.TRANSIENT_LOCAL
        qos_profile.durability = QoSHistoryPolicy.KEEP_LAST

        self.subscription = self.create_subscription(
            String,
            "/mujoco_robot_description_preprocessed",
            self.listener_callback,
            qos_profile=qos_profile,
        )
        self.publisher = self.create_publisher(String, "/mujoco_robot_description", qos_profile=qos_profile)

        self.get_logger().info("Waiting for /mujoco_robot_description_preprocessed topic.")

    def listener_callback(self, msg: String):
        dom = minidom.parseString(msg.data)

        compiler_element = dom.getElementsByTagName("compiler")[0]
        mesh_dir = compiler_element.getAttribute("meshdir")
        asset_dir = mesh_dir.removesuffix("/")
        base_dir = os.path.dirname(asset_dir)

        if self.copy_assets:
            # copy the cylinder mockup into the assets directory
            shutil.copy2(
                f"{get_package_share_directory('phoebe_mujoco_config')}/resources/cylinder_mockup_full_length.stl",
                f"{asset_dir}",
            )

            # copy the cylinder jig into the assets directory (folder bc it has several files bc it is decomposed)
            os.mkdir(f"{asset_dir}/cylinder_jig")
            shutil.copytree(
                f"{get_package_share_directory('phoebe_mujoco_config')}/resources/cylinder_jig",
                f"{asset_dir}/cylinder_jig",
                dirs_exist_ok=True,
            )

            # copy the april tags into the assets directory
            shutil.copy2(
                f"{get_package_share_directory('phoebe_mujoco_config')}/resources/tag36_11_00000.png",
                f"{asset_dir}",
            )
            shutil.copy2(
                f"{get_package_share_directory('phoebe_mujoco_config')}/resources/tag36_11_00001.png",
                f"{asset_dir}",
            )
            shutil.copy2(
                f"{get_package_share_directory('phoebe_mujoco_config')}/resources/tag36_11_00004.png",
                f"{asset_dir}",
            )
            shutil.copy2(
                f"{get_package_share_directory('phoebe_mujoco_config')}/resources/tag36_11_00006.png",
                f"{asset_dir}",
            )

        # Get all elements with the tag name body
        body_elements = dom.getElementsByTagName("body")

        # Replace the wheels with the custom wheels xml if specified
        if not self.magic_carpet:

            # add the mesh mecanum_wheel_22.stl to the assets
            asset_elements = dom.getElementsByTagName("asset")
            asset_element = asset_elements[0]

            mecanum_wheel_element = dom.createElement("mesh")
            mecanum_wheel_element.setAttribute("file", "mecanum_wheel_22.stl")
            mecanum_wheel_element.setAttribute("scale", "0.001 0.001 0.001")
            asset_element.appendChild(mecanum_wheel_element)

            # copy the mecanum wheel 22 mesh into the assets directory
            shutil.copy2(
                f"{get_package_share_directory('phoebe_mujoco_config')}/resources/mecanum_wheel_22.stl",
                f"{asset_dir}",
            )

            include_element = dom.createElement("include")
            include_element.setAttribute("file", f"{base_dir}/wheels.xml")

            shutil.copy2(
                f"{get_package_share_directory(self.wheels_package)}/description/wheels.xml",
                f"{base_dir}",
            )

            # Filter by attribute value containing a substring
            first_time = True
            for elem in body_elements:
                if "wheel_link" in elem.getAttribute("name"):
                    if first_time:
                        elem.parentNode.replaceChild(include_element, elem)
                        first_time = False
                    else:
                        elem.parentNode.removeChild(elem)

        # replace the right hand with the custom modified xml that
        # has working 2f-85 mechanism
        if self.right_gripper == "2f85":
            right_include_element = dom.createElement("include")
            right_include_element.setAttribute("file", f"{base_dir}/right_robotiq_85.xml")

            # Filter by attribute value containing a substring
            first_time_right = True
            for elem in body_elements:
                if "right_robotiq_85" in elem.getAttribute("name"):
                    if first_time_right:
                        elem.parentNode.replaceChild(right_include_element, elem)
                        first_time_right = False
                    else:
                        elem.parentNode.removeChild(elem)

            # copy in the robotiq_85 xml file into the main mujoco description directory
            # and process it through xacro to resolve the tf_prefix argument
            right_robotiq_xacro_src = (
                f"{get_package_share_directory('phoebe_mujoco_config')}/resources/right_robotiq_85.xml"
            )
            right_robotiq_output = f"{base_dir}/right_robotiq_85.xml"
            subprocess.run(
                [
                    "xacro",
                    right_robotiq_xacro_src,
                    f"tf_prefix:={self.tf_prefix}",
                ],
                stdout=open(right_robotiq_output, "w"),
                check=True,
            )

        if self.left_gripper == "2f85":
            left_include_element = dom.createElement("include")
            left_include_element.setAttribute("file", f"{base_dir}/left_robotiq_85.xml")

            # Filter by attribute value containing a substring
            first_time_left = True
            for elem in body_elements:
                if "left_robotiq_85" in elem.getAttribute("name"):
                    if first_time_left:
                        elem.parentNode.replaceChild(left_include_element, elem)
                        first_time_left = False
                    else:
                        elem.parentNode.removeChild(elem)

            # copy in the robotiq_85 xml file into the main mujoco description directory
            # and process it through xacro to resolve the tf_prefix argument
            left_robotiq_xacro_src = (
                f"{get_package_share_directory('phoebe_mujoco_config')}/resources/left_robotiq_85.xml"
            )
            left_robotiq_output = f"{base_dir}/left_robotiq_85.xml"
            subprocess.run(
                [
                    "xacro",
                    left_robotiq_xacro_src,
                    f"tf_prefix:={self.tf_prefix}",
                ],
                stdout=open(left_robotiq_output, "w"),
                check=True,
            )

        xml_data = "\n".join([line for line in dom.toprettyxml(indent="  ").splitlines() if line.strip()])

        # remove the first line bc MuJoCo doesn't like the xml tag at the beginning
        modified_lines = xml_data.splitlines(True)
        modified_lines.pop(0)
        modified_data = "".join(modified_lines)

        out_msg = String()
        out_msg.data = modified_data

        self.publisher.publish(out_msg)

        self.get_logger().info("Published post-processed mjcf to /mujoco_robot_description")


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Generate wheels for PB mujoco sim",
    )
    parser.add_argument("--tf-prefix", default="", help="tf_prefix for generated wheels")
    parser.add_argument(
        "--magic-carpet",
        action="store_true",
        default=False,
        help="Skip wheel replacement if running in magic carpet mode",
    )
    parser.add_argument(
        "--wheels-package",
        default="phoebe_mujoco_config",
        help="Package containing wheels.xml, should be the top level deploy package",
    )
    parser.add_argument(
        "--left-gripper",
        default="hande",
        help="gripper type for the left side (either hande or 2f85)",
    )
    parser.add_argument(
        "--right-gripper",
        default="hande",
        help="gripper type for the right side (either hande or 2f85)",
    )
    parser.add_argument(
        "--copy-assets",
        action="store_true",
        default=False,
        help="Whether or not to include assets (cylinders / apriltags) in the processing",
    )

    # Skip ros args
    non_ros_args = rclpy.utilities.remove_ros_args(sys.argv)[1:]
    parsed_args = parser.parse_args(non_ros_args)

    tf_prefix = parsed_args.tf_prefix
    magic_carpet = parsed_args.magic_carpet
    wheels_package = parsed_args.wheels_package
    left_gripper = parsed_args.left_gripper
    right_gripper = parsed_args.right_gripper
    copy_assets = parsed_args.copy_assets

    rclpy.init(args=args)
    node = StringModifierNode(tf_prefix, magic_carpet, wheels_package, left_gripper, right_gripper, copy_assets)
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
