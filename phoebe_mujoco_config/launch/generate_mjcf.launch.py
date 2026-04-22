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
from launch.event_handlers import OnProcessExit, OnShutdown
from launch.actions import RegisterEventHandler, DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition, UnlessCondition


def generate_launch_description():

    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "use_pregenerated_assets_dir",
            default_value="false",
            description="Use pre-generated assets dir. This is useful if you are just modifying an existing structure",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_left_static_pedestal",
            default_value="false",
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


    # this version can be run for general
    # make_mjcf_from_robot_description = Node(
    #     package="mujoco_ros2_control",
    #     executable="make_mjcf_from_robot_description.py",
    #     output="screen",
    #     arguments=default_arguments,
    #     condition=UnlessCondition(LaunchConfiguration("use_pregenerated_assets_dir")),
    # )

    def launch_mjcf_node(context):
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".urdf", delete=False)
        tmp.write(robot_description_content.perform(context))
        tmp.close()

        default_arguments = [
            "--urdf",
            tmp.name,
            "-c",  # convert stl to obj
            # "-f",  # first link fixed --> free
            "--save_only",
        ]

        args_with_assets_dir = default_arguments + [
            "--asset_dir",
            PathJoinSubstitution([FindPackageShare(phoebe_mujoco_package_name), "description", "assets"]),
        ]

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
                arguments=default_arguments,
                condition=UnlessCondition(use_pregenerated_assets_dir),
            ),
            Node(
                package="mujoco_ros2_control",
                executable="make_mjcf_from_robot_description.py",
                output="both",
                emulate_tty=True,
                arguments=args_with_assets_dir,
                condition=IfCondition(use_pregenerated_assets_dir),
            ),
            # This waits for the topic /mujoco_robot_description_preprocessed to be published, then takes the data,
            # post-processes it, and writes out the modified data to /mujoco_robot_description. This handles some
            # special components like wheels, custom robotiq gripper mujoco representations, april tags, etc

            RegisterEventHandler(OnShutdown(on_shutdown=cleanup)),
        ]

    generate_mjcf = OpaqueFunction(function=launch_mjcf_node)

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

    # delay_post_process = RegisterEventHandler(
    #     OnProcessExit(target_action=generate_mjcf, on_exit=[post_process_mjcf])
    # )

    return LaunchDescription(
        declared_arguments
        + [
           generate_mjcf,
           post_process_mjcf,
           wheel_code_gen,
        ] 
    )
