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
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    control_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("phoebe_deploy"),
                "launch",
                "control.launch.py",
            )
        ),
        launch_arguments={
            "use_fake_hardware": "true",
            "robot_description_package": "phoebe_mujoco_config",
            "robot_description_file": "phoebe_xacro.urdf",
            "use_sim_time": "true",
        }.items(),
    )

    teleop_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("phoebe_deploy"),
                "launch",
                "teleop.launch.py",
            )
        ),
        launch_arguments={
            "joystick_dev": "/dev/input/js0",
        }.items(),
    )

    return LaunchDescription([control_launch, teleop_launch])
