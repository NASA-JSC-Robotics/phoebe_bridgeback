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
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterFile
# import logging
# logging.root.setLevel(logging.DEBUG)


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
            "tf_prefix",
            default_value="",
            description="tf_prefix of the joint names, useful for \
        multi-robot setup. If changed, also joint names in the controllers' configuration \
        have to be updated.",
        )
    )
    namespace = LaunchConfiguration("namespace")
    default_ns = "ridgeback"
    tf_prefix = LaunchConfiguration("tf_prefix")
    tf_prefix = tf_prefix  # dummy use to get precommit to be happy

    # Include Packages
    pkg_phoebe_deploy = FindPackageShare("phoebe_deploy")
    pkg_phoebe_safety = FindPackageShare("phoebe_safety")
    pkg_clearpath_ros2_socketcan_interface = FindPackageShare("clearpath_ros2_socketcan_interface")
    pkg_clearpath_ros2_socketcan_interface = FindPackageShare("clearpath_ros2_socketcan_interface")
    pkg_clearpath_diagnostics = FindPackageShare("clearpath_diagnostics")
    pkg_clearpath_firmware = FindPackageShare("clearpath_firmware")
    pkg_proton = FindPackageShare("proton_ros2")

    # config files
    config_can = PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback", "can_config.yaml"])
    setup_path = PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback"])

    # Declare launch files
    launch_arg_diagnostic_updater_params = DeclareLaunchArgument(
        'diagnostic_updater_params',
        default_value=PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback", "diagnostic_updater.yaml"]),
        description='')

    diagnostic_updater_params = LaunchConfiguration('diagnostic_updater_params')

    launch_arg_diagnostic_aggregator_params = DeclareLaunchArgument(
        'diagnostic_aggregator_params',
        default_value=PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback", "diagnostic_aggregator.yaml"]),
        description='')

    diagnostic_aggregator_params = LaunchConfiguration('diagnostic_aggregator_params')


    launch_file_receiver = PathJoinSubstitution(
        [pkg_clearpath_ros2_socketcan_interface, "launch", "receiver.launch.py"]
    )
    launch_file_sender = PathJoinSubstitution([pkg_clearpath_ros2_socketcan_interface, "launch", "sender.launch.py"])
    launch_file_phoebe_safety = PathJoinSubstitution([pkg_phoebe_safety, "launch", "phoebe_safety_manager.launch.py"])
    launch_file_proton = PathJoinSubstitution([pkg_proton, "launch", "proton_ros2.launch.py"])
    launch_file_diagnostics = PathJoinSubstitution([pkg_clearpath_diagnostics, 'launch', 'diagnostics.launch.py'])


    launch_receiver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([launch_file_receiver]),
        launch_arguments={
            "namespace": default_ns,
            "interface": "vcan0",
            "from_can_bus_topic": "vcan0/rx",
        }.items(),
    )
    launch_sender = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([launch_file_sender]),
        launch_arguments={
            "namespace": default_ns,
            "interface": "vcan0",
            "to_can_bus_topic": "vcan0/tx",
        }.items(),
    )
    launch_phoebe_safety = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([launch_file_phoebe_safety]),
    )
    launch_proton = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([launch_file_proton]),
        launch_arguments={
            "config_file": PathJoinSubstitution([pkg_clearpath_firmware, "proton", "r100.yaml"]),
            "target": "pc",
            "namespace": default_ns
        }.items(),
    )

    # launch_diagnostics = IncludeLaunchDescription(
    #     PythonLaunchDescriptionSource([launch_file_diagnostics]),
    #     launch_arguments={
    #             'namespace': default_ns,
    #             'updater_parameters': diagnostic_updater_params,
    #             'aggregator_parameters': diagnostic_aggregator_params,
    #     }
    # )

    # Nodes
    node_wireless_watcher = Node(
        name="wireless_watcher",
        executable="wireless_watcher",
        package="wireless_watcher",
        namespace=default_ns,
        output="screen",
        parameters=[
            {
                "hz": 1.0,
                "dev": "",
                "connected_topic": "platform/wifi_connected",
                "connection_topic": "platform/wifi_status",
            },
        ],
    )

    node_battery_state_estimator = Node(
        name="battery_state_estimator",
        executable="battery_state_estimator",
        package="clearpath_hardware_interfaces",
        namespace=default_ns,
        output="screen",
        parameters=[{ 'tf_prefix': tf_prefix }],
        arguments=[
            "-s",
            setup_path,
        ],
    )

    node_battery_state_control = Node(
        name="battery_state_control",
        executable="battery_state_control",
        package="clearpath_hardware_interfaces",
        namespace=default_ns,
        output="screen",
        parameters=[{ 'tf_prefix': tf_prefix }],        
        arguments=[
            "-s",
            setup_path,
        ],
    )

    node_lighting_node = Node(
        name="lighting_node",
        executable="lighting_node",
        package="clearpath_hardware_interfaces",
        namespace=default_ns,
        output="screen",
        parameters=[
            {
                "platform": "r100",
            },
        ],
    )

    node_puma_control = Node(
        name="puma_control",
        executable="multi_puma_node",
        package="puma_motor_driver",
        namespace=default_ns,
        output="screen",
        parameters=[
            ParameterFile(config_can, allow_substs=True),
        ],
        remappings=[
            ("platform/puma/cmd", "platform/puma/cmd_throttle"),
            ("platform/puma/feedback", "/platform/puma/feedback"),
        ],
    )

    # node_aggregator_node = Node(
    #     package="diagnostic_aggregator",
    #     executable="aggregator_node",
    #     namespace=default_ns,
    #     output="screen",
    #     parameters=[analyzer_params],
    #     remappings=[
    #         ("/diagnostics", "diagnostics"),
    #         ("/diagnostics_agg", "diagnostics_agg"),
    #         ("/diagnostics_toplevel_state", "diagnostics_toplevel_state"),
    #     ],
    # )

    # node_diagnostics_updater = Node(
    #     package="clearpath_diagnostics",
    #     executable="diagnostics_updater",
    #     namespace=default_ns,
    #     output="screen",
    #     remappings=[
    #         ("/diagnostics", "diagnostics"),
    #         ("/diagnostics_agg", "diagnostics_agg"),
    #         ("/diagnostics_toplevel_state", "diagnostics_toplevel_state"),
    #     ],
    #     arguments=["-s", setup_path],
    # )

    # launch_args = [
    #     launch_arg_diagnostic_aggregator_params,
    #     launch_arg_diagnostic_updater_params
    # ]

    launches = [
        launch_receiver,
        launch_sender,
        launch_phoebe_safety,
        launch_proton,
        # launch_diagnostics
    ]
    nodes = [
        node_wireless_watcher,
        # Comment out pending addressing the $(var stuff) in robot.yaml.
        # node_battery_state_estimator,
        # node_battery_state_control,
        node_lighting_node,
        node_puma_control,
    ]
    processes = []

    ns_action = GroupAction(actions=[PushRosNamespace(namespace)] + launches + nodes + processes)
    # ns_action = GroupAction(actions=[PushRosNamespace(namespace)] + launch_args + launches + nodes + processes)

    return LaunchDescription(declared_arguments + [ns_action])
