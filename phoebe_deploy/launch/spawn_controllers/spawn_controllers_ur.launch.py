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

    namespace = LaunchConfiguration("namespace")
    is_sim = LaunchConfiguration("is_sim")

    nodes = []

    # Grouped by (condition, namespace) since both are set per spawner process, not per
    # controller. NOTE: the forward_*/friction_model controllers already didn't pass
    # namespace=namespace before this change. Preserved as-is rather than silently fixing it.
    unconditional_controllers = [
        {"name": "right_force_torque_sensor_broadcaster"},
        {"name": "right_ur_joint_trajectory_controller"},
        {"name": "left_force_torque_sensor_broadcaster"},
        {"name": "left_ur_joint_trajectory_controller"},
    ]
    nodes.append(spawn_controllers(unconditional_controllers, namespace=namespace))

    unconditional_no_namespace_controllers = [
        {"name": "left_forward_position_controller", "inactive": True},
        {"name": "left_forward_velocity_controller", "inactive": True},
        {"name": "left_forward_effort_controller", "inactive": True},
        {"name": "right_forward_position_controller", "inactive": True},
        {"name": "right_forward_velocity_controller", "inactive": True},
        {"name": "right_forward_effort_controller", "inactive": True},
    ]
    nodes.append(spawn_controllers(unconditional_no_namespace_controllers))

    hardware_only_controllers = [
        {"name": "right_io_and_status_controller"},
        {"name": "right_freedrive_mode_controller", "inactive": True},
        {"name": "left_io_and_status_controller"},
        {"name": "left_freedrive_mode_controller", "inactive": True},
    ]
    nodes.append(spawn_controllers(hardware_only_controllers, namespace=namespace, condition=UnlessCondition(is_sim)))

    hardware_only_no_namespace_controllers = [
        {"name": "left_friction_model_controller", "inactive": True},
        {"name": "right_friction_model_controller", "inactive": True},
    ]
    nodes.append(spawn_controllers(hardware_only_no_namespace_controllers, condition=UnlessCondition(is_sim)))

    return LaunchDescription(declared_arguments + nodes)
