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
from launch.substitutions import LaunchConfiguration
from launch.conditions import UnlessCondition

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

    namespace = LaunchConfiguration("namespace")
    is_sim = LaunchConfiguration("is_sim")

    nodes = []

    nodes.append(
        spawn_controller("right_io_and_status_controller", namespace=namespace, condition=UnlessCondition(is_sim))
    )
    nodes.append(spawn_controller("right_force_torque_sensor_broadcaster", namespace=namespace))
    nodes.append(spawn_controller("right_ur_joint_trajectory_controller", namespace=namespace))
    nodes.append(
        spawn_controller(
            "right_freedrive_mode_controller", namespace=namespace, inactive=True, condition=UnlessCondition(is_sim)
        )
    )
    nodes.append(
        spawn_controller("left_io_and_status_controller", namespace=namespace, condition=UnlessCondition(is_sim))
    )
    nodes.append(spawn_controller("left_force_torque_sensor_broadcaster", namespace=namespace))
    nodes.append(spawn_controller("left_ur_joint_trajectory_controller", namespace=namespace))
    nodes.append(
        spawn_controller(
            "left_freedrive_mode_controller", namespace=namespace, inactive=True, condition=UnlessCondition(is_sim)
        )
    )
    nodes.append(spawn_controller("left_forward_effort_controller", inactive=True))
    nodes.append(spawn_controller("left_friction_model_controller", inactive=True))
    nodes.append(spawn_controller("right_forward_effort_controller", inactive=True))
    nodes.append(spawn_controller("right_friction_model_controller", inactive=True))

    return LaunchDescription(declared_arguments + nodes)
