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
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterFile


def generate_launch_description():

    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "tf_prefix",
            default_value="",
            description="tf_prefix of the joint names, useful for \
        multi-robot setup. If changed, also joint names in the controllers' configuration \
        have to be updated.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "namespace",
            default_value="",
            description="Namespace for the hardware robot",
        )
    )

    # Initialize Arguments
    namespace = LaunchConfiguration("namespace")

    # helper function to make controller nodes
    def MakeControllerNode(controller_name):
        return Node(
            package="controller_manager",
            executable="spawner",
            name=controller_name,
            arguments=[
                "--controller-manager",
                "controller_manager",
                "--controller-manager-timeout",
                "300",
                "--namespace",
                namespace,
                controller_name,
            ],
            output="screen",
        )

    # helper function to get controllers files that we might need
    def GetControllersFile(file_name):
        return PathJoinSubstitution(
            [
                get_package_share_directory("phoebe_deploy"),
                "config",
                file_name,
            ]
        )

    # launch controller manager

    # contains update rate
    controllers_common = GetControllersFile("controllers_common.yaml")
    # controllers for the ridgeback
    controllers_r100 = GetControllersFile("controllers_r100.yaml")

    nodes = []

    # start the controller manager node with all of the controller config files
    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        namespace=namespace,
        # allow_substs allows tf_prefix to be pulled in
        parameters=[
            ParameterFile(controllers_common, allow_substs=True),
            ParameterFile(controllers_r100, allow_substs=True),
        ],
        remappings=[
            # remap to be able to use the global robot_description
            ("~/robot_description", "robot_description"),
            # Necessary remap for platform velocity controller. Preferably this would be done
            # at spawn time. This is not supported in humble, but is supported in jazzy.
        ],
        output="both",
    )

    node_puma_throttle = Node(
        name="puma_throttle",
        executable="throttle",
        package="topic_tools",
        namespace=namespace,
        output="screen",
        arguments=["messages", "platform/puma/cmd", "50", "ridgeback/platform/puma/cmd_throttle"],
    )

    platform_velocity_controller = MakeControllerNode("platform_velocity_controller")
    joint_state_broadcaster = MakeControllerNode("joint_state_broadcaster")

    nodes = [control_node, node_puma_throttle, platform_velocity_controller, joint_state_broadcaster]

    return LaunchDescription(declared_arguments + nodes)
