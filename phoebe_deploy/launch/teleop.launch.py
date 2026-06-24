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
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterFile


def generate_launch_description():
    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "namespace",
            default_value="",
            description="Namespace for the robot.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_sim_time", choices=["true", "false"], default_value="false", description="Use simulation time"
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument("joystick_dev", default_value="/dev/input/js0", description="dev location of joystick")
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "launch_joystick",
            choices=["true", "false"],
            default_value="true",
            description="Whether or not to launch the joystick device",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "reference_topic",
            default_value="platform_velocity_controller/reference",
            description="Command outputs from the muxer",
        )
    )

    # Launch Configurations
    namespace = LaunchConfiguration("namespace")
    use_sim_time = LaunchConfiguration("use_sim_time")
    joystick_dev = LaunchConfiguration("joystick_dev")
    launch_joystick = LaunchConfiguration("launch_joystick")
    reference_topic = LaunchConfiguration("reference_topic")

    # Include Packages
    pkg_phoebe_deploy = FindPackageShare("phoebe_deploy")
    pkg_phoebe_safety = FindPackageShare("phoebe_safety")

    # config files
    config_teleop_joy = PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback", "teleop_joy.yaml"])
    config_twist_mux = PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback", "twist_mux.yaml"])
    config_teleop_interactive_markers = PathJoinSubstitution(
        [pkg_phoebe_deploy, "config", "ridgeback", "teleop_interactive_markers.yaml"]
    )

    config_joystick_safing = PathJoinSubstitution([pkg_phoebe_safety, "config", "pb_joystick_actions.yaml"])

    node_joy = Node(
        package="joy_linux",
        executable="joy_linux_node",
        namespace=namespace,
        output="screen",
        name="joy_node",
        parameters=[
            config_teleop_joy,
            {
                "use_sim_time": use_sim_time,
                "dev": joystick_dev,
            },
        ],
        remappings=[
            ("/diagnostics", "diagnostics"),
            ("/tf", "tf"),
            ("/tf_static", "tf_static"),
            ("joy", "joy_teleop/joy"),
            ("joy/set_feedback", "joy_teleop/joy/set_feedback"),
        ],
        condition=IfCondition(launch_joystick),
    )

    node_teleop_twist_joy = Node(
        package="teleop_twist_joy",
        executable="teleop_node",
        namespace=namespace,
        output="screen",
        name="teleop_twist_joy_node",
        parameters=[
            config_teleop_joy,
            {"use_sim_time": use_sim_time},
        ],
        remappings=[
            ("joy", "joy_teleop/joy"),
            ("cmd_vel", "joy_teleop/cmd_vel"),
        ],
    )

    node_interactive_marker_twist_server = Node(
        package="interactive_marker_twist_server",
        executable="marker_server",
        namespace=namespace,
        name="twist_server_node",
        remappings=[
            ("cmd_vel", "twist_marker_server/cmd_vel"),
            ("twist_server/feedback", "twist_marker_server/feedback"),
            ("twist_server/update", "twist_marker_server/update"),
        ],
        parameters=[config_teleop_interactive_markers, {"use_sim_time": use_sim_time}],
        output="screen",
    )
    node_twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        namespace=namespace,
        output="screen",
        remappings={
            ("/cmd_vel_out", reference_topic),
            ("/diagnostics", "diagnostics"),
            ("/tf", "tf"),
            ("/tf_static", "tf_static"),
        },
        parameters=[
            ParameterFile(config_twist_mux, allow_substs=True),
            {"use_sim_time": use_sim_time}
        ],
    )

    node_joystick_safing = Node(
        package="phoebe_safety",
        executable="pb_joystick_safing.py",
        namespace=namespace,
        output="screen",
        name="pb_joystick_safing",
        parameters=[
            {"actions_file": config_joystick_safing},
        ],
        condition=IfCondition(launch_joystick),
    )

    nodes = [
        node_joy,
        node_teleop_twist_joy,
        node_interactive_marker_twist_server,
        node_twist_mux,
        node_joystick_safing,
    ]

    return LaunchDescription(declared_arguments + nodes)
