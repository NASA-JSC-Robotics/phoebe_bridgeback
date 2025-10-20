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
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

# Test launch file for joystick safing. This launch file launches a joystick safing
# node with a test config file set up to support generation of successful and
# failed service requests and functions.


def generate_launch_description():
    # Launch configurations
    actions_file = LaunchConfiguration("actions_file")
    axis_tolerance = LaunchConfiguration("axis_tolerance")

    return LaunchDescription(
        [
            # Declare launch arguments
            DeclareLaunchArgument(
                "actions_file",
                default_value=PathJoinSubstitution(
                    [FindPackageShare("phoebe_safety"), "config", "test_pb_joystick_actions.yaml"]
                ),
                description="Path to joystick actions file",
            ),
            DeclareLaunchArgument(
                "axis_tolerance", default_value="0.01", description="How much axis movement constitutes 'movement'"
            ),
            # Start the safety manager node
            Node(
                package="phoebe_safety",
                executable="pb_joystick_safing.py",
                name="pb_joystick_safing",
                output="both",
                parameters=[
                    {"actions_file": actions_file},
                    {"axis_tolerance": axis_tolerance},
                ],
            ),
        ]
    )
