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
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition

from phoebe_deploy.launch_helpers import spawn_controller


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
            "is_sim",
            default_value="false",
            description="This is some kind of simulation environment",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "include_world_joints",
            default_value="false",
            description="Whether or not to include a root world frame and run phoebe on a magic carpet",
            choices=["true", "false"],
        )
    )

    namespace = LaunchConfiguration("namespace")
    is_sim = LaunchConfiguration("is_sim")
    include_world_joints = LaunchConfiguration("include_world_joints")

    # Use wheels if not using the magic carpet
    wheel_controllers = GroupAction(
        condition=UnlessCondition(include_world_joints),
        actions=[
            # For some reason, in sim, we have to set the wheel radius to ~0.063 for it to behave realistically.
            # This should definitely be investigated further.
            spawn_controller(
                "platform_velocity_controller",
                namespace=namespace,
                condition=IfCondition(is_sim),
            ),
            spawn_controller(
                "platform_velocity_controller",
                namespace=namespace,
                condition=UnlessCondition(is_sim),
            ),
            spawn_controller(
                "odom_publisher",
                namespace=namespace,
                condition=IfCondition(is_sim),
            ),
            spawn_controller(
                "odom_publisher",
                namespace=namespace,
                condition=UnlessCondition(is_sim),
            ),
            spawn_controller(
                "imu_broadcaster",
                namespace=namespace,
                condition=IfCondition(is_sim),
            ),
        ],
    )

    magic_carpet_controller = GroupAction(
        condition=IfCondition(include_world_joints),
        actions=[
            spawn_controller(
                "phoebe_magic_carpet_controller",
                namespace=namespace,
                condition=IfCondition(is_sim),
            ),
        ],
        # NOTE: We explicitly exclude odom since the rails provide perfect ground truth
    )

    return LaunchDescription(declared_arguments + [wheel_controllers, magic_carpet_controller])
