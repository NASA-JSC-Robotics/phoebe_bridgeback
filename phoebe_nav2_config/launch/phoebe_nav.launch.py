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


from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.actions import IncludeLaunchDescription, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch.conditions import IfCondition, UnlessCondition
from launch_ros.actions import Node, PushRosNamespace, SetRemap


def generate_launch_description():
    pkg_phoebe_nav2_config = get_package_share_directory("phoebe_nav2_config")
    pkg_phoebe_deploy = get_package_share_directory("phoebe_deploy")

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
            "tf_prefix",
            default_value="",
            description="tf_prefix of the joint names, useful for \
        multi-robot setup. If changed, also joint names in the controllers' configuration \
        have to be updated.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "launch_rviz",
            default_value="true",
            description="Launch rviz or nah",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "rviz_config_file",
            default_value=PathJoinSubstitution(
                [get_package_share_directory("phoebe_nav2_config"), "rviz", "slam_test.rviz"]
            ),
            description="Full path to an rviz config file for bringup",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_sim_time",
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
    declared_arguments.append(
        DeclareLaunchArgument(
            "magic_carpet",
            default_value="false",
            description="Use ground-truth odometry from virtual joints as Phoebe is on a magic carpet ride",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "nav2_config_file",
            default_value=PathJoinSubstitution([pkg_phoebe_nav2_config, "config", "clearpath_nav2_config.yaml"]),
            description="Full path for the nav2 stack config file.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "localization_config_file",
            default_value=PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback", "localization.yaml"]),
            description="Full path for the localization yaml config file.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "slam_config_file",
            default_value=PathJoinSubstitution([pkg_phoebe_nav2_config, "config/", "clearpath_slam_config.yaml"]),
            description="Full path for a slam config yaml file, only used when publishing tf",
        )
    )

    namespace = LaunchConfiguration("namespace")
    tf_prefix = LaunchConfiguration("tf_prefix")
    launch_rviz = LaunchConfiguration("launch_rviz")
    rviz_config_file = LaunchConfiguration("rviz_config_file")
    use_sim_time = LaunchConfiguration("use_sim_time")
    publish_tf = LaunchConfiguration("publish_tf")
    magic_carpet = LaunchConfiguration("magic_carpet")
    nav2_config_file = LaunchConfiguration("nav2_config_file")
    localization_config_file = LaunchConfiguration("localization_config_file")
    slam_config_file = LaunchConfiguration("slam_config_file")

    rviz_qss_file = PathJoinSubstitution([get_package_share_directory("phoebe_moveit_config"), "config", "dark.qss"])

    nodes_to_start = [
        # Use a copied version of https://github.com/SteveMacenski/slam_toolbox/blob/ros2/launch/online_async_launch.py,
        # as the upstream does not support yaml param substitutions. Added as part of namespace / tf_prefix support for
        # nav2 launches in: https://github.com/NASA-JSC-Robotics/phoebe_bridgeback/pull/43/
        # SLAM and localization are skipped in magic carpet mode. Instead we rely on the magic carpet controller
        # to connect odom -> base_link, and a static transform publisher in place of slam.
        GroupAction(
            condition=UnlessCondition(magic_carpet),
            actions=[
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        [PathJoinSubstitution([pkg_phoebe_nav2_config, "launch", "online_async_launch.py"])]
                    ),
                    launch_arguments={
                        "tf_prefix": tf_prefix,
                        "slam_params_file": slam_config_file,
                        "use_sim_time": use_sim_time,
                    }.items(),
                    condition=IfCondition(publish_tf),
                ),
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        [PathJoinSubstitution([(pkg_phoebe_nav2_config), "launch", "online_async_launch.py"])]
                    ),
                    launch_arguments={
                        "tf_prefix": tf_prefix,
                        "slam_params_file": PathJoinSubstitution(
                            [pkg_phoebe_nav2_config, "config/clearpath_slam_config_no_tf.yaml"]
                        ),
                        "use_sim_time": use_sim_time,
                    }.items(),
                    condition=UnlessCondition(publish_tf),
                ),
            ],
        ),
        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            name="map_to_odom_identity",
            arguments=["0", "0", "0", "0", "0", "0", "map", "odom"],
            parameters=[{"use_sim_time": use_sim_time}],
            condition=IfCondition(magic_carpet),
        ),
        # Use custom nav launch file for tf prefixing fix
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [PathJoinSubstitution([(pkg_phoebe_nav2_config), "launch", "navigation_launch.py"])]
            ),
            launch_arguments={
                "namespace": "",
                "tf_prefix": tf_prefix,
                "params_file": nav2_config_file,
                "use_sim_time": use_sim_time,
            }.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [PathJoinSubstitution([(pkg_phoebe_deploy), "launch", "ridgeback_sensors.launch.py"])]
            ),
            launch_arguments={
                "namespace": "",
                "tf_prefix": tf_prefix,
                "is_sim": use_sim_time,
                "publish_tf": publish_tf,
                "localization_config": localization_config_file,
            }.items(),
            condition=UnlessCondition(magic_carpet),
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
        ),
        # Launch the odom to joint state publisher if needed for other planning applications.
        Node(
            package="phoebe_deploy",
            executable="odometry_joint_state_publisher.py",
            name="odometry_joint_state_publisher",
            parameters=[{"use_sim_time": use_sim_time}],
            condition=UnlessCondition(publish_tf),
        ),
    ]

    # Namespaces are pushed down by this group action, so don't namespace anything directly
    # above or you end up with duplicates.
    ns_action = GroupAction(
        actions=[
            PushRosNamespace(namespace),
            SetRemap(src="tf_static", dst="/tf_static"),
            SetRemap(src="tf", dst="/tf"),
        ]
        + nodes_to_start
    )

    return LaunchDescription(declared_arguments + [ns_action])
