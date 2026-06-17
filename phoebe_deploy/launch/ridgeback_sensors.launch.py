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
from launch.conditions import UnlessCondition
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterFile


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
            "publish_tf",
            default_value="True",
            description="Whether or not to publish tf from slam, defaults to False."
            "If False, users must manually handle map -> odom -> base_link transforms.",
        )
    )

    namespace = LaunchConfiguration("namespace")
    is_sim = LaunchConfiguration("is_sim")
    publish_tf = LaunchConfiguration("publish_tf")
    default_ns = "ridgeback"

    # Include Packages
    pkg_phoebe_deploy = FindPackageShare("phoebe_deploy")
    pkg_clearpath_sensors = FindPackageShare("clearpath_sensors")

    config_imu_filter = PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback", "imu_filter.yaml"])
    config_localization = PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback", "localization.yaml"])
    config_lidar2d = PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback", "lidar2d_0.yaml"])

    launch_file_hokuyo_ust = PathJoinSubstitution([pkg_clearpath_sensors, "launch", "hokuyo_ust.launch.py"])

    # Include Packages
    pkg_clearpath_sensors = FindPackageShare("clearpath_sensors")

    # Include launch files
    launch_hokuyo_ust = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([launch_file_hokuyo_ust]),
        launch_arguments={
            "parameters": config_lidar2d,
            "namespace": f"{default_ns}/sensors/lidar2d_0",
        }.items(),
        condition=UnlessCondition(is_sim),
    )

    node_imu_filter_madgwick = Node(
        name="imu_filter_madgwick",
        executable="imu_filter_madgwick_node",
        package="imu_filter_madgwick",
        namespace=default_ns,
        output="screen",
        remappings=[
            ("imu/data_raw", "sensors/imu_0/data_raw"),
            ("imu/mag", "sensors/imu_0/magnetic_field"),
            ("imu/data", "sensors/imu_0/data"),
            ("/tf", "tf"),
        ],
        parameters=[
            ParameterFile(config_imu_filter, allow_substs=True),
        ],
        condition=UnlessCondition(is_sim),
    )

    node_localization = Node(
        package="robot_localization",
        executable="ekf_node",
        name="ekf_node",
        namespace=default_ns,
        output="screen",
        parameters=[
            ParameterFile(config_localization, allow_substs=True),
            {
                "use_sim_time": is_sim,
                "publish_tf": publish_tf,
            },
        ],
        remappings=[
            ("~/odometry/filtered", "platform/odom/filtered"),
            ("~/diagnostics", "diagnostics"),
            ("~/tf", "tf"),
            ("~/tf_static", "tf_static"),
        ],
    )

    launches = [
        launch_hokuyo_ust,
    ]
    nodes = [
        node_imu_filter_madgwick,
        node_localization,
    ]

    ns_action = GroupAction(actions=[PushRosNamespace(namespace)] + launches + nodes)

    return LaunchDescription(declared_arguments + [ns_action])
