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


import os
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch.conditions import IfCondition, UnlessCondition


def generate_launch_description():
    pkg_phoebe_nav2_config = get_package_share_directory("phoebe_nav2_config")
    pkg_slam_toolbox = get_package_share_directory("slam_toolbox")
    pkg_nav2_bringup = get_package_share_directory("nav2_bringup")
    pkg_phoebe_deploy = get_package_share_directory("phoebe_deploy")

    # Use static map in sim because sensor data is not available.

    declared_arguments = [
        DeclareLaunchArgument(
            "launch_rviz",
            default_value="true",
            description="Launch rviz or nah",
        ),
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="false",
            description="This is some kind of simulation environment",
        ),
    ]
    declared_arguments.append(
        DeclareLaunchArgument(
            "publish_tf",
            default_value="True",
            description="Whether or not to publish tf from slam, defaults to False."
                        "If False, users must manually handle map -> odom -> base_link transforms.",
        )
    )

    launch_rviz = LaunchConfiguration("launch_rviz")
    use_sim_time = LaunchConfiguration("use_sim_time")
    publish_tf = LaunchConfiguration("publish_tf")

    rviz_config_file = os.path.join(get_package_share_directory("phoebe_nav2_config"), "rviz", "slam_test.rviz")
    rviz_qss_file = os.path.join(get_package_share_directory("phoebe_moveit_config"), "config", "dark.qss")

    nodes_to_start = [
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [PathJoinSubstitution([(pkg_slam_toolbox), "launch", "online_async_launch.py"])]
            ),
            launch_arguments={
                "slam_params_file": os.path.join(pkg_phoebe_nav2_config, "config/clearpath_slam_config.yaml"),
                "use_sim_time": use_sim_time,
            }.items(),
            condition=IfCondition(publish_tf),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [PathJoinSubstitution([(pkg_slam_toolbox), "launch", "online_async_launch.py"])]
            ),
            launch_arguments={
                "slam_params_file": os.path.join(pkg_phoebe_nav2_config, "config/clearpath_slam_config_no_tf.yaml"),
                "use_sim_time": use_sim_time,
            }.items(),
            condition=UnlessCondition(publish_tf),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [PathJoinSubstitution([(pkg_nav2_bringup), "launch", "navigation_launch.py"])]
            ),
            launch_arguments={
                "params_file": os.path.join(pkg_phoebe_nav2_config, "config/clearpath_nav2_config.yaml"),
                "use_sim_time": use_sim_time,
            }.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [PathJoinSubstitution([(pkg_phoebe_deploy), "launch", "ridgeback_sensors.launch.py"])]
            ),
            launch_arguments={
                "is_sim": use_sim_time,
                "publish_tf": publish_tf,
            }.items(),
        ),
        Node(
            package="rviz2",
            executable="rviz2",
            name="rviz2_nav2",
            output="log",
            arguments=["-d", rviz_config_file, "--stylesheet", rviz_qss_file],
            condition=IfCondition(launch_rviz),
            parameters=[{"use_sim_time": use_sim_time}],
        ),
        Node(
            package="phoebe_deploy",
            executable="world_publisher.py",
            name="world_publisher",
            parameters=[{"use_sim_time": use_sim_time}],
            condition=IfCondition(publish_tf),
        ),
    ]

    return LaunchDescription(declared_arguments + nodes_to_start)
