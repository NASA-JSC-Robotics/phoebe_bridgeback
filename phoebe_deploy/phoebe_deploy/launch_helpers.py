#!/usr/bin/env python3
#
# Copyright (c) 2026, United States Government, as represented by the
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

from launch.substitutions import (
    LaunchConfiguration,
)
from launch_ros.actions import Node


def spawn_controller(
    controller_name,
    inactive=False,
    controller_manager_name="controller_manager",
    timeout=300,
    namespace: LaunchConfiguration = "",
    condition=None,
):
    """
    Create a spawn controller node action for the specified controller and arguments.
    """
    inactive_flags = ["--inactive"] if inactive else []

    return Node(
        package="controller_manager",
        executable="spawner",
        name=controller_name,
        namespace=namespace,
        arguments=[
            controller_name,
            "--controller-manager",
            controller_manager_name,
            "--controller-manager-timeout",
            str(timeout),
        ]
        + inactive_flags,
        output="both",
        condition=condition,
    )
