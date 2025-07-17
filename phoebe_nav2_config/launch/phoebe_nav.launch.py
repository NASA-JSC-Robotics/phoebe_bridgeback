#!/usr/bin/env python3
import os
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, TextSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    pkg_phoebe_nav2_config = get_package_share_directory("phoebe_nav2_config")
    pkg_slam_toolbox = get_package_share_directory("slam_toolbox")
    pkg_nav2_bringup = get_package_share_directory("nav2_bringup")
    lifecycle_nodes = ['map_server']

    # Use static map in sim because sensor data is not available.

    declared_arguments = [
        DeclareLaunchArgument(
            'map',
            default_value=os.path.join(pkg_phoebe_nav2_config,
                                       'maps', 'test.yaml'),
            description='Path to static map to use',
        ),
    ]
    map = LaunchConfiguration('map')

    rviz_config_file = os.path.join(get_package_share_directory("phoebe_nav2_config"), "rviz", "slam_test.rviz")
    rviz_qss_file = os.path.join(get_package_share_directory("phoebe_moveit_config"), "config", "dark.qss")

    nodes_to_start = [
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                PathJoinSubstitution([
                    (pkg_slam_toolbox),
                    'launch',
                    'online_async_launch.py'
                ])
            ]),
            launch_arguments={
                'slam_params_file': os.path.join(pkg_phoebe_nav2_config, 'config/clearpath_slam_config.yaml')
            }.items()
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=['0','0','0','0','0','0','map','world'],
            # condition=UnlessCondition(OrSubstitution(LaunchConfiguration('slam'),LaunchConfiguration('amcl'))),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                PathJoinSubstitution([
                    (pkg_nav2_bringup),
                    'launch',
                    'navigation_launch.py'
                ])
            ]),
            launch_arguments={
                'params_file': os.path.join(pkg_phoebe_nav2_config, 'config/clearpath_nav2_config.yaml')
            }.items()
        ),
        Node(
            package="rviz2",
            executable="rviz2",
            name="rviz2_nav2",
            output="log",
            arguments=["-d", rviz_config_file, "--stylesheet", rviz_qss_file],
        ),
    ]

    return LaunchDescription(declared_arguments + nodes_to_start)
 