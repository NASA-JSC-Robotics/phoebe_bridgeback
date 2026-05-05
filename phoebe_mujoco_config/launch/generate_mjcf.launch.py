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
from launch_ros.actions import Node
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.substitutions import FindPackageShare
from launch.event_handlers import OnShutdown, OnProcessExit
from launch.actions import RegisterEventHandler, DeclareLaunchArgument, OpaqueFunction


def generate_launch_description():

    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "use_pregenerated_assets_dir",
            default_value="false",
            choices=["true", "false"],
            description="Use pre-generated assets dir. This is useful if you are just modifying an existing structure",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_left_static_pedestal",
            default_value="false",
            choices=["true", "false"],
            description="Replace left ewellix lift kit with static pedestal.",
        )
    )

    phoebe_mujoco_package_name = "phoebe_mujoco_config"
    phoebe_mujoco_description_file = "phoebe_mujoco_xacro.urdf"

    use_left_static_pedestal = LaunchConfiguration("use_left_static_pedestal")
    use_pregenerated_assets_dir = LaunchConfiguration("use_pregenerated_assets_dir")

    # main robot description for Phoebe
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [
                    FindPackageShare(phoebe_mujoco_package_name),
                    "urdf",
                    phoebe_mujoco_description_file,
                ]
            ),
            " add_grasp_push_frames:=false",
            " use_left_static_pedestal:=",
            use_left_static_pedestal,
        ]
    )

    def launch_mjcf_node(context):
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".urdf", delete=False)
        tmp.write(robot_description_content.perform(context))
        tmp.close()

        default_arguments = [
            "--urdf",
            tmp.name,
            "-c",  # convert stl to obj
            "--save_only",
        ]

        if use_pregenerated_assets_dir.perform(context) == "true":
            default_arguments = default_arguments + [
                "--asset_dir",
                PathJoinSubstitution([FindPackageShare(phoebe_mujoco_package_name), "description", "assets"]),
            ]

        generate_mjcf = Node(
            package="mujoco_ros2_control",
            executable="make_mjcf_from_robot_description.py",
            output="both",
            emulate_tty=True,
            arguments=default_arguments,
        )

        post_process_mjcf = Node(
            package="phoebe_mujoco_config",
            executable="post_process_mjcf.py",
            output="screen",
        )

        wheel_code_gen = Node(
            package="phoebe_mujoco_config",
            executable="wheel_code_gen.py",
            output="screen",
        )

        # Ensure the file gets deleted
        def cleanup(event, context):
            if os.path.exists(tmp.name):
                os.remove(tmp.name)

        return [
            generate_mjcf,
            wheel_code_gen,
            RegisterEventHandler(OnProcessExit(target_action=generate_mjcf, on_exit=[post_process_mjcf])),
            RegisterEventHandler(OnShutdown(on_shutdown=cleanup)),
        ]

    generate_mjcf = OpaqueFunction(function=launch_mjcf_node)

    return LaunchDescription(
        declared_arguments
        + [
            generate_mjcf,
        ]
    )
