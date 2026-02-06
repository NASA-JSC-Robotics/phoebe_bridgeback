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


def generate_launch_description():

    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "ns",
            default_value="",
            description="Namespace for the hardware robot",
        )
    )

    ns = LaunchConfiguration("ns")

    nodes = []

    # helper function to make controller nodes
    def MakeControllerNode(controller_name, active=True, condition=None):
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

        return Node(
            package="controller_manager",
            executable="spawner",
            name=controller_name,
            arguments=arguments,
            output="screen",
            condition=condition,
        )

    nodes.append(MakeControllerNode("left_admittance_controller", active=False))
    nodes.append(MakeControllerNode("left_admittance_jtc", active=False))
    nodes.append(MakeControllerNode("left_force_torque_sensor_broadcaster_admittance", active=False))
    nodes.append(MakeControllerNode("right_admittance_controller", active=False))
    nodes.append(MakeControllerNode("right_admittance_jtc", active=False))
    nodes.append(MakeControllerNode("right_force_torque_sensor_broadcaster_admittance", active=False))
    # nodes.append(MakeControllerNode("dual_arm_admittance_jtc", active=False))

    return LaunchDescription(declared_arguments + nodes)
