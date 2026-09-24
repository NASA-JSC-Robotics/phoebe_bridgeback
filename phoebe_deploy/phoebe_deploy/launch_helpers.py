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


def spawn_controllers(
    controllers,
    controller_manager_name="controller_manager",
    timeout=300,
    namespace: LaunchConfiguration = "",
    condition=None,
):
    """
    Create a single spawner node action that loads every controller in `controllers`.

    Each entry in `controllers` is either a controller name (str) or a dict with keys
    "name" (required), "inactive" (bool, default False), and "controller_ros_args"
    (str, optional). Uses the spawner's "--controller <name> [opts]" advanced mode so each
    controller keeps its own inactive/ros-args settings within the one spawner process.
    `condition` applies to the whole node, so controllers that must be spawned under different
    conditions belong in separate spawn_controllers() calls.
    """
    arguments = [
        "--controller-manager",
        controller_manager_name,
        "--controller-manager-timeout",
        str(timeout),
    ]
    for controller in controllers:
        if isinstance(controller, str):
            controller = {"name": controller}
        arguments += ["--controller", controller["name"]]
        if controller.get("inactive"):
            arguments.append("--inactive")
        if controller.get("controller_ros_args") is not None:
            arguments += ["--controller-ros-args", controller["controller_ros_args"]]

    return Node(
        package="controller_manager",
        executable="spawner",
        namespace=namespace,
        arguments=arguments,
        output="both",
        condition=condition,
    )
