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
            "include_world_joints",
            default_value="false",
            description="Whether or not to include a root world frame",
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

    # Initialize Arguments
    namespace = LaunchConfiguration("namespace")
    calibration_mode = LaunchConfiguration("calibration_mode")
    include_world_joints = LaunchConfiguration("include_world_joints")
    use_left_static_pedestal = LaunchConfiguration("use_left_static_pedestal")

    control_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory("phoebe_deploy"), "launch", "control.launch.py")
        ),
        launch_arguments={
            "use_fake_hardware": "false",
            "namespace": namespace,
            "calibration_mode": calibration_mode,
            "include_world_joints": include_world_joints,
            "use_left_static_pedestal": use_left_static_pedestal,
        }.items(),
    )

    teleop_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory("phoebe_deploy"), "launch", "teleop.launch.py")
        ),
        launch_arguments={
            "namespace": namespace,
        }.items(),
    )

    return LaunchDescription(declared_arguments + [control_launch, teleop_launch])
