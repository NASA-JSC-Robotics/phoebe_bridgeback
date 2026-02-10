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
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    arguments = []

    arguments.append(
        DeclareLaunchArgument(
            "tf_prefix",
            default_value='""',
            description="tf_prefix of the joint names, useful for \
        multi-robot setup. If changed, also joint names in the controllers' configuration \
        have to be updated.",
        )
    )
    arguments.append(
        DeclareLaunchArgument(
            "is_sim",
            default_value="false",
            description="Start robot with simulated hardware mirroring command to its states.",
        )
    )
    arguments.append(
        DeclareLaunchArgument(
            "headless_mode",
            default_value="false",
            description="Enable headless mode for robot control",
        )
    )
    arguments.append(
    DeclareLaunchArgument(
            "use_left_static_pedestal",
            default_value="false",
            description="Replaces the left liftkit with the static pedestal",
        )
    )

    # Initialize Arguments
    tf_prefix = LaunchConfiguration("tf_prefix")
    is_sim = LaunchConfiguration("is_sim")
    headless_mode = LaunchConfiguration("headless_mode")
    use_left_static_pedestal = LaunchConfiguration("use_left_static_pedestal")

    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution([FindPackageShare("phoebe_description"), "urdf", "phoebe.urdf.xacro"]),
            " ",
            "tf_prefix:=",
            tf_prefix,
            " ",
            "is_sim:=",
            is_sim,
            " ",
            "headless_mode:=",
            headless_mode,
            " ",
            "use_left_static_pedestal:=",
            use_left_static_pedestal,
            " ",
        ]
    )
    robot_description = {"robot_description": robot_description_content}

    rviz_config_file = PathJoinSubstitution([FindPackageShare("phoebe_description"), "rviz", "view_robot.rviz"])

    joint_state_broadcaster = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description],
    )
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
    )

    nodes = [
        joint_state_broadcaster,
        robot_state_publisher,
        rviz_node,
    ]

    return LaunchDescription(arguments + nodes)
