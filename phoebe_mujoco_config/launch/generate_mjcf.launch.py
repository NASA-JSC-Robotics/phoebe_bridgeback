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


from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.substitutions import FindPackageShare
from launch.event_handlers import OnProcessExit
from launch.actions import RegisterEventHandler, DeclareLaunchArgument
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
            description="Use pre-generated assets dir. This is useful if you are just modifying an existing structure",
        )
    )

    phoebe_mujoco_package_name = "phoebe_mujoco_config"
    phoebe_mujoco_description_file = "phoebe_mujoco_xacro.urdf"

    use_left_static_pedestal = LaunchConfiguration("use_left_static_pedestal")

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

    default_arguments = [
        "-r",
        robot_description_content,
        "-c",  # convert stl to obj
        "-f",
        "--save_only",
    ]

    args_with_assets_dir = default_arguments + [
        "--asset_dir",
        PathJoinSubstitution([FindPackageShare(phoebe_mujoco_package_name), "description", "assets"]),
    ]

    # this version can be run for general
    make_mjcf_from_robot_description = Node(
        package="mujoco_ros2_control",
        executable="make_mjcf_from_robot_description.py",
        output="screen",
        arguments=default_arguments,
        condition=UnlessCondition(LaunchConfiguration("use_pregenerated_assets_dir")),
    )

    make_mjcf_from_robot_description_use_assets_dir = Node(
        package="mujoco_ros2_control",
        executable="make_mjcf_from_robot_description.py",
        output="screen",
        arguments=args_with_assets_dir,
        condition=IfCondition(LaunchConfiguration("use_pregenerated_assets_dir")),
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

    delay_post_process = RegisterEventHandler(
        OnProcessExit(target_action=make_mjcf_from_robot_description, on_exit=[post_process_mjcf])
    )

    return LaunchDescription(
        declared_arguments
        + [
            make_mjcf_from_robot_description,
            make_mjcf_from_robot_description_use_assets_dir,
            delay_post_process,
            wheel_code_gen,
        ]
    )
