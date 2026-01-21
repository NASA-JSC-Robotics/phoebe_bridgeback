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
from launch_ros.actions import Node
from launch.substitutions import (
    Command,
    FindExecutable,
    PathJoinSubstitution,
)
from launch_ros.substitutions import FindPackageShare
from launch.event_handlers import OnProcessExit
from launch.actions import RegisterEventHandler


def generate_launch_description():

    phoebe_mujoco_package_name = "phoebe_mujoco_config"
    phoebe_mujoco_description_file = "phoebe_xacro.urdf"
    phoebe_mujoco_package_path = get_package_share_directory(phoebe_mujoco_package_name)

    mujoco_inputs = os.path.join(phoebe_mujoco_package_path, "description", "mujoco_inputs.xml")

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
            " ",
            "add_grasp_push_frames:=",
            "false",
        ]
    )

    make_mjcf_from_robot_description = Node(
        package="mujoco_ros2_control",
        executable="make_mjcf_from_robot_description.py",
        output="screen",
        arguments=[
            "-r",
            robot_description_content,
            "-m",
            mujoco_inputs,
            "-c",  # convert stl to obj
            "-f",
            "--save_only",
        ],
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
        [
            make_mjcf_from_robot_description,
            delay_post_process,
            wheel_code_gen,
        ]
    )
