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
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    LaunchConfiguration,
)
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "namespace",
            default_value="",
            description="Namespace for the hardware robot",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "calibration_mode",
            default_value="false",
            description="Whether or not we are running the calibration routine",
            choices=["true", "false"],
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_left_static_pedestal",
            default_value="false",
            description="Replaces the left liftkit with the static pedestal",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "left_hand_type",
            default_value="hande",
            choices=["hande"],
            description="Hand type to put on the left arm of phoebe. Only hande is supported for mock_hardware at this moment",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "right_hand_type",
            default_value="hande",
            choices=["hande"],
            description="Hand type to put on the right arm of phoebe. Only hande is supported for mock_hardware at this moment",
        )
    )

    # Initialize Arguments
    namespace = LaunchConfiguration("namespace")
    calibration_mode = LaunchConfiguration("calibration_mode")
    use_left_static_pedestal = LaunchConfiguration("use_left_static_pedestal")
    left_hand_type = LaunchConfiguration("left_hand_type")
    right_hand_type = LaunchConfiguration("right_hand_type")
    control_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory("phoebe_deploy"), "launch", "control.launch.py")
        ),
        launch_arguments={
            "use_fake_hardware": "true",
            "namespace": namespace,
            "calibration_mode": calibration_mode,
            "use_left_static_pedestal": use_left_static_pedestal,
            "left_hand_type": left_hand_type,
            "right_hand_type": right_hand_type,
        }.items(),
    )

    return LaunchDescription(declared_arguments + [control_launch])
