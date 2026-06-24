#!/usr/bin/env python3
#
# Copyright (c) 2025, United States Government, as represented by the
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


import os
import tempfile

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, IncludeLaunchDescription, RegisterEventHandler
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.event_handlers import OnShutdown
from launch.substitutions import (
    PathJoinSubstitution,
    LaunchConfiguration,
    Command,
    FindExecutable,
)
from launch_ros.substitutions import FindPackageShare
from launch.conditions import UnlessCondition
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "point_clouds",
            default_value="True",
            description="Whether or not to include the point cloud republishers, must be using polled cameras",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "include_world_joints",
            default_value="false",
            description="Whether or not to include a root world frame",
            choices=["true", "false"],
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_pregenerated_mjcf",
            default_value="false",
            description="Use pre-generated mjcf instead of converting it on the fly.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "sim_speed",
            default_value="1.0",
            description="Percentage speed to run the simulation at. 1.0 is 100 percent speed.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_left_static_pedestal",
            default_value="false",
            description="Whether to use the left static pedestal instead of the left lift",
            choices=["true", "false"],
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "left_hand_type",
            default_value="hande",
            choices=["hande", "2f85"],
            description="Hand type to put on the left arm of phoebe",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "right_hand_type",
            default_value="hande",
            choices=["hande", "2f85"],
            description="Hand type to put on the right arm of phoebe",
        )
    )

    point_clouds = LaunchConfiguration("point_clouds")
    include_world_joints = LaunchConfiguration("include_world_joints")
    use_pregenerated_mjcf = LaunchConfiguration("use_pregenerated_mjcf")
    sim_speed = LaunchConfiguration("sim_speed")
    use_left_static_pedestal = LaunchConfiguration("use_left_static_pedestal")
    left_hand_type = LaunchConfiguration("left_hand_type")
    right_hand_type = LaunchConfiguration("right_hand_type")

    phoebe_mujoco_package_name = "phoebe_mujoco_config"
    phoebe_mujoco_description_file = "phoebe_mujoco_xacro.urdf"

    mjcf_robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [FindPackageShare(phoebe_mujoco_package_name), "urdf", phoebe_mujoco_description_file]
            ),
            # Grasp frames should not be converted to MJCF objects
            " add_grasp_push_frames:=false",
            " model_mobile_env:=true",
            " include_scene_objects:=true",
            " base_joint_type:=floating",
            " use_left_static_pedestal:=",
            use_left_static_pedestal,
            " left_hand_type:=",
            left_hand_type,
            " right_hand_type:=",
            right_hand_type,
        ]
    )

    # Using an inline opaque function to write the URDF for mujoco to a tempfile...
    # This prevents it from being dumped into the console on conversion errors.
    def launch_mjcf_node(context):
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".urdf", delete=False)
        tmp.write(mjcf_robot_description_content.perform(context))
        tmp.close()

        # Ensure the file gets deleted
        def cleanup(event, context):
            if os.path.exists(tmp.name):
                os.remove(tmp.name)

        return [
            # Writing to /mujoco_robot_description_preprocessed instead of /mujoco_robot_description because the
            # we need to do some post-processing before we can actually use the output. See node below for more details
            Node(
                package="mujoco_ros2_control",
                executable="make_mjcf_from_robot_description.py",
                output="both",
                emulate_tty=True,
                arguments=[
                    # "-f",
                    "--publish_topic",
                    "/mujoco_robot_description_preprocessed",
                    "--urdf",
                    tmp.name,
                    "--convert_stl_to_obj",
                    "--asset_dir",
                    PathJoinSubstitution([FindPackageShare(phoebe_mujoco_package_name), "description", "assets"]),
                ],
                condition=UnlessCondition(use_pregenerated_mjcf),
            ),
            # This waits for the topic /mujoco_robot_description_preprocessed to be published, then takes the data,
            # post-processes it, and writes out the modified data to /mujoco_robot_description. This handles some
            # special components like wheels, custom robotiq gripper mujoco representations, april tags, etc
            Node(
                package="phoebe_mujoco_config",
                executable="post_process_mjcf_runtime.py",
                name="post_process_mjcf_runtime",
                arguments=[
                    "--left-gripper",
                    left_hand_type,
                    "--right-gripper",
                    right_hand_type,
                ],
            ),
            RegisterEventHandler(OnShutdown(on_shutdown=cleanup)),
        ]

    generate_mjcf = OpaqueFunction(function=launch_mjcf_node)

    extra_xacro_args = [
        " use_pregenerated_mjcf:=",
        use_pregenerated_mjcf,
        " sim_speed:=",
        sim_speed,
        " model_mobile_env:=false",
    ]

    extra_controller_params_file = PathJoinSubstitution(
        [FindPackageShare(phoebe_mujoco_package_name), "config", "mujoco_plugins.yaml"]
    )

    # Include the control launch file with relevant configuration
    control_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("phoebe_deploy"),
                "launch",
                "control.launch.py",
            )
        ),
        launch_arguments={
            "use_fake_hardware": "true",
            "robot_description_package": "phoebe_mujoco_config",
            "robot_description_file": "phoebe_mujoco_xacro.urdf",
            "use_sim_time": "true",
            "include_world_joints": include_world_joints,
            "use_left_static_pedestal": use_left_static_pedestal,
            "extra_xacro_args": extra_xacro_args,
            "left_hand_type": left_hand_type,
            "right_hand_type": right_hand_type,
            "extra_controller_params_file": extra_controller_params_file,
        }.items(),
    )

    # Launch teleoperation for joystick control
    teleop_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("phoebe_deploy"),
                "launch",
                "teleop.launch.py",
            )
        ),
        launch_arguments={
            "joystick_dev": "/dev/input/js0",
        }.items(),
    )

    nodes = []

    nodes.append(
        Node(
            package="depth_image_proc",
            executable="point_cloud_xyzrgb_node",
            name="left_point_cloud_proc_node",
            parameters=[
                {
                    "use_sim_time": True,
                    "use_exact_sync": False,
                }
            ],
            remappings=[
                ("rgb/image_rect_color", "/left_wrist_mounted_camera/color/image_raw"),
                ("rgb/camera_info", "/left_wrist_mounted_camera/color/camera_info"),
                ("depth_registered/image_rect", "/left_wrist_mounted_camera/aligned_depth_to_color/image_raw"),
                ("points", "/left_wrist_mounted_camera/depth/color/points"),
            ],
            condition=IfCondition(point_clouds),
        )
    )

    nodes.append(
        Node(
            package="depth_image_proc",
            executable="point_cloud_xyzrgb_node",
            name="right_point_cloud_proc_node",
            parameters=[
                {
                    "use_sim_time": True,
                    "use_exact_sync": False,
                }
            ],
            remappings=[
                ("rgb/image_rect_color", "/right_wrist_mounted_camera/color/image_raw"),
                ("rgb/camera_info", "/right_wrist_mounted_camera/color/camera_info"),
                ("depth_registered/image_rect", "/right_wrist_mounted_camera/aligned_depth_to_color/image_raw"),
                ("points", "/right_wrist_mounted_camera/depth/color/points"),
            ],
            condition=IfCondition(point_clouds),
        )
    )

    return LaunchDescription(declared_arguments + [generate_mjcf, control_launch, teleop_launch] + nodes)
