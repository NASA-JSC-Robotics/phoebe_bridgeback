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

from phoebe_deploy.launch_helpers import spawn_controllers


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
            "magic_carpet",
            default_value="false",
            description="Whether or not Phoebe is on a magic carpet, affects controller spawning.",
            choices=["true", "false"],
        )
    )

    namespace = LaunchConfiguration("namespace")
    is_sim = LaunchConfiguration("is_sim")
    magic_carpet = LaunchConfiguration("magic_carpet")

    # Use wheels if not using the magic carpet. platform_velocity_controller and odom_publisher
    # share the same is_sim condition in each branch, so each branch is spawned together.
    wheel_controllers = GroupAction(
        condition=UnlessCondition(magic_carpet),
        actions=[
            # For some reason, in sim, we have to set the wheel radius to ~0.063 for it to behave realistically.
            # This should definitely be investigated further.
            spawn_controllers(
                [
                    {
                        "name": "platform_velocity_controller",
                        "controller_ros_args": "--ros-args -p kinematics.wheels_radius:=0.063",
                    },
                    {
                        "name": "odom_publisher",
                        "controller_ros_args": "--ros-args -p kinematics.wheels_radius:=0.063",
                    },
                ],
                namespace=namespace,
                condition=IfCondition(is_sim),
            ),
            spawn_controllers(
                [{"name": "platform_velocity_controller"}, {"name": "odom_publisher"}],
                namespace=namespace,
                condition=UnlessCondition(is_sim),
            ),
        ],
    )

    # Always spawn an IMU broadcaster
    imu_broadcaster = spawn_controllers(
        [
            {
                "name": "imu_broadcaster",
                "controller_ros_args": "--ros-args --remap /imu_broadcaster/imu:=sensors/imu_0/data_raw",
            }
        ],
        namespace=namespace,
        condition=IfCondition(is_sim),
    )

    wheels_joint_state_broadcaster = spawn_controllers(
        [{"name": "wheels_joint_state_broadcaster"}],
        namespace=namespace,
    )

    # Magic carpet replaces both the wheel controllers and filters on odom, so publish directly
    # and have it connect tf.
    magic_carpet_controller = GroupAction(
        condition=IfCondition(magic_carpet),
        actions=[
            spawn_controllers(
                [
                    {
                        "name": "phoebe_magic_carpet_controller",
                        "controller_ros_args": "--ros-args"
                        " --remap /phoebe_magic_carpet_controller/odom:=/ridgeback/odometry/filtered",
                    }
                ],
                namespace=namespace,
                condition=IfCondition(is_sim),
            ),
        ],
    )

    return LaunchDescription(
        declared_arguments
        + [wheel_controllers, imu_broadcaster, wheels_joint_state_broadcaster, magic_carpet_controller]
    )
