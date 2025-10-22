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
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    # Launch configurations
    robot_side = LaunchConfiguration("robot_side")

    return LaunchDescription(
        [
            # Declare launch arguments
            DeclareLaunchArgument(
                "robot_side",
                default_value="right",
                description="Which robot arm is doing the calibration",
                choices=["left", "right"],
            ),
            # Start the safety manager node
            Node(
                package="phoebe_calibration",  # <-- Replace with your actual package name
                executable="phoebe_calibration.py",  # Make sure this matches your installed script name
                name="phoebe_calibration",
                output="both",
                parameters=[
                    {"robot_side": robot_side},
                ],
            ),
        ]
    )
