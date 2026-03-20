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
from launch.substitutions import (
    LaunchConfiguration,
)
from launch_ros.actions import Node
from launch.conditions import IfCondition, UnlessCondition


def generate_launch_description():

    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "ns",
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

    ns = LaunchConfiguration("ns")
    is_sim = LaunchConfiguration("is_sim")

    nodes = []

    # helper function to make controller nodes
    def MakeControllerNode(controller_name, active=True, condition=None, controller_ros_args=None):
        arguments = [
            "--controller-manager",
            "controller_manager",
            "--controller-manager-timeout",
            "300",
            "--namespace",
            ns,
            controller_name,
        ]
        if not active:
            arguments.append("--inactive")
        if controller_ros_args is not None:
            for controller_ros_arg in controller_ros_args:
                arguments.append("--controller-ros-args")
                arguments.append(f"{controller_ros_arg}")

        return Node(
            package="controller_manager",
            executable="spawner",
            name=controller_name,
            arguments=arguments,
            output="screen",
            condition=condition,
        )

    # For some reason, in sim, we have to set the wheel radius to ~0.063 for it to behave realistically.
    # This should definitely be investigated further.
    nodes.append(
        MakeControllerNode(
            "platform_velocity_controller",
            condition=IfCondition(is_sim),
            controller_ros_args=[
                "--ros-args -p kinematics.wheels_radius:=0.063",
            ],
        )
    )
    nodes.append(
        MakeControllerNode(
            "platform_velocity_controller",
            condition=UnlessCondition(is_sim),
        )
    )
    nodes.append(MakeControllerNode("odom_publisher"))
    nodes.append(
        MakeControllerNode(
            "imu_broadcaster",
            condition=IfCondition(is_sim),
            controller_ros_args=[
                "--ros-args --remap /imu_broadcaster/imu:=/ridgeback/sensors/imu_0/data_raw",
            ],
        )
    )

    return LaunchDescription(declared_arguments + nodes)
