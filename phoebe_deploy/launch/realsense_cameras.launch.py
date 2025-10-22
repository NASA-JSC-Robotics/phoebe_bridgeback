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

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():

    left_camera = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory("realsense2_camera"), "launch", "rs_launch.py")
        ),
        launch_arguments={
            "camera_name": "left_wrist_mounted_camera",
            "camera_namespace": "",
            "serial_no": "'207522078043'",
            "rgb_camera.color_profile": "1280,720,6",
            # "depth_module.depth_profile": "320,180,6",
            # "depth_module.infra_profile": "320,180,6",
            "initial_reset": "true",
            "pointcloud.enable": "false",
            "align_depth.enable": "false",
            "enable_depth": "false",
        }.items(),
    )

    right_camera = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory("realsense2_camera"), "launch", "rs_launch.py")
        ),
        launch_arguments={
            "camera_name": "right_wrist_mounted_camera",
            "camera_namespace": "",
            "serial_no": "'207522073775'",  # needs to be updated for actual serial number
            "rgb_camera.color_profile": "1280,720,6",
            # "depth_module.depth_profile": "320,180,6",
            # "depth_module.infra_profile": "320,180,6",
            "initial_reset": "true",
            "pointcloud.enable": "false",
            "align_depth.enable": "false",
            "enable_depth": "false",
        }.items(),
    )

    return LaunchDescription([left_camera, right_camera])
    # return LaunchDescription([right_camera])
