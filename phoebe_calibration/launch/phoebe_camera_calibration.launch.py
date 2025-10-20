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
from launch_ros.substitutions import FindPackageShare
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.parameter_descriptions import ParameterFile


def generate_launch_description():
    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "config_filename",
            default_value="left_camera_config.yaml",
            description="which camera filename to run",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "namespace",
            default_value="left_wrist_mounted_camera",
            description="namespace - make sure this matches the camera name",
        )
    )

    config_filename = LaunchConfiguration("config_filename")
    namespace = LaunchConfiguration("namespace")

    config_filepath = PathJoinSubstitution(
        [
            FindPackageShare("phoebe_calibration"),
            "config",
            config_filename,
        ]
    )

    hand_eye_cal = Node(
        name="hand_eye_cal",
        namespace=namespace,
        package="hand_eye_cal_ros2",
        executable="hand_eye_cal_node",
        remappings=[
            ("color_image", "color/image_raw"),
            ("camera_info", "color/camera_info"),
        ],
        output="screen",
        parameters=[ParameterFile(config_filepath)],
    )

    return LaunchDescription(declared_arguments + [hand_eye_cal])
