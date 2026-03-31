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

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from xml.dom import minidom
import os
import shutil
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy, QoSHistoryPolicy
from ament_index_python.packages import get_package_share_directory


class StringModifierNode(Node):
    def __init__(self):
        super().__init__("string_modifier_node")

        # Subscriber
        self.subscription = self.create_subscription(
            String, "/mujoco_robot_description_preprocessed", self.listener_callback, 10
        )

        # Publisher

        qos_profile = QoSProfile(depth=1)
        qos_profile.reliability = QoSReliabilityPolicy.RELIABLE
        qos_profile.durability = QoSDurabilityPolicy.TRANSIENT_LOCAL
        qos_profile.durability = QoSHistoryPolicy.KEEP_LAST
        self.publisher = self.create_publisher(String, "/mujoco_robot_description", qos_profile=qos_profile)

        self.get_logger().info("Waiting for /mujoco_robot_description_preprocessed topic.")

    def listener_callback(self, msg: String):
        dom = minidom.parseString(msg.data)

        compiler_element = dom.getElementsByTagName("compiler")[0]
        mesh_dir = compiler_element.getAttribute("meshdir")
        asset_dir = mesh_dir.removesuffix("/")
        base_dir = os.path.dirname(asset_dir)

        # copy the cylinder mockup into the assets directory
        shutil.copy2(
            f'{get_package_share_directory("phoebe_mujoco_config")}/resources/cylinder_mockup_full_length.stl',
            f"{asset_dir}",
        )

        # copy the cylinder jig into the assets directory (folder bc it has several files bc it is decomposed)
        os.mkdir(f"{asset_dir}/cylinder_jig")
        shutil.copytree(
            f'{get_package_share_directory("phoebe_mujoco_config")}/resources/cylinder_jig',
            f"{asset_dir}/cylinder_jig",
            dirs_exist_ok=True,
        )

        # copy the april tags into the assets directory
        shutil.copy2(
            f'{get_package_share_directory("phoebe_mujoco_config")}/resources/tag36_11_00000.png',
            f"{asset_dir}",
        )
        shutil.copy2(
            f'{get_package_share_directory("phoebe_mujoco_config")}/resources/tag36_11_00001.png',
            f"{asset_dir}",
        )
        shutil.copy2(
            f'{get_package_share_directory("phoebe_mujoco_config")}/resources/tag36_11_00004.png',
            f"{asset_dir}",
        )
        shutil.copy2(
            f'{get_package_share_directory("phoebe_mujoco_config")}/resources/tag36_11_00006.png',
            f"{asset_dir}",
        )

        # add the mesh mecanum_wheel_22.stl to the assets
        asset_elements = dom.getElementsByTagName("asset")
        asset_element = asset_elements[0]

        mecanum_wheel_element = dom.createElement("mesh")
        mecanum_wheel_element.setAttribute("file", "mecanum_wheel_22.stl")
        mecanum_wheel_element.setAttribute("scale", "0.001 0.001 0.001")
        asset_element.appendChild(mecanum_wheel_element)

        # copy the mecanum wheel 22 mesh into the assets directory
        shutil.copy2(
            f'{get_package_share_directory("phoebe_mujoco_config")}/resources/mecanum_wheel_22.stl',
            f"{asset_dir}",
        )

        # Replace the wheels with the custom wheels xml
        # Get all elements with the tag name body
        body_elements = dom.getElementsByTagName("body")

        include_element = dom.createElement("include")
        include_element.setAttribute("file", f"{base_dir}/wheels.xml")

        shutil.copy2(
            f'{get_package_share_directory("phoebe_mujoco_config")}/description/wheels.xml',
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
        include_element = dom.createElement("include")
        include_element.setAttribute("file", f"{base_dir}/right_robotiq_85.xml")

        # Filter by attribute value containing a substring
        first_time = True
        for elem in body_elements:
            if "right_robotiq_85" in elem.getAttribute("name"):
                if first_time:
                    elem.parentNode.replaceChild(include_element, elem)
                    first_time = False
                else:
                    elem.parentNode.removeChild(elem)

        # copy in the robotiq_85 xml file into the main mujoco description directory
        shutil.copy2(
            f'{get_package_share_directory("phoebe_mujoco_config")}/resources/right_robotiq_85.xml',
            f"{base_dir}",
        )

        xml_data = "\n".join([line for line in dom.toprettyxml(indent="  ").splitlines() if line.strip()])

        # remove the first line bc MuJoCo doesn't like the xml tag at the beginning
        modified_lines = xml_data.splitlines(True)
        modified_lines.pop(0)
        modified_data = "".join(modified_lines)

        out_msg = String()
        out_msg.data = modified_data

        self.publisher.publish(out_msg)

        self.get_logger().info(f"Published post-processed mjcf to /mujoco_robot_description")


def main(args=None):
    rclpy.init(args=args)
    node = StringModifierNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
