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
from launch_ros.parameter_descriptions import ParameterFile


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
            default_value="slam_test.rviz",
            description="Which RViz config file to use",
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
            "reference_topic",
            default_value="platform_velocity_controller/reference",
            description="Command outputs from the muxer. Namespace is applied on top of it.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "nav2_config_file",
            default_value="clearpath_nav2_config.yaml",
            description="File name for nav2 config yaml file",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "localization_config_file",
            default_value="localization.yaml",
            description="File name for the localization yaml config file, use the namespaced/prefixed if necessary",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "slam_config_file",
            default_value="clearpath_slam_config.yaml",
            description="Filename for a slam config yaml file, only used when publishing tf",
        )
    )

    namespace = LaunchConfiguration("namespace")
    tf_prefix = LaunchConfiguration("tf_prefix")
    launch_rviz = LaunchConfiguration("launch_rviz")
    rviz_config_file = LaunchConfiguration("rviz_config_file")
    use_sim_time = LaunchConfiguration("use_sim_time")
    publish_tf = LaunchConfiguration("publish_tf")
    reference_topic = LaunchConfiguration("reference_topic")
    nav2_config_file = LaunchConfiguration("nav2_config_file")
    localization_config_file = LaunchConfiguration("localization_config_file")
    slam_config_file = LaunchConfiguration("slam_config_file")

    localization_config = (PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback", localization_config_file]),)
    config_twist_mux = PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback", "twist_mux.yaml"])
    rviz_config_file = PathJoinSubstitution(
        [get_package_share_directory("phoebe_nav2_config"), "rviz", rviz_config_file]
    )
    rviz_qss_file = PathJoinSubstitution([get_package_share_directory("phoebe_moveit_config"), "config", "dark.qss"])

    nodes_to_start = [
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [PathJoinSubstitution([pkg_phoebe_nav2_config, "launch", "online_async_launch.py"])]
            ),
            launch_arguments={
                "tf_prefix": tf_prefix,
                "slam_params_file": PathJoinSubstitution([pkg_phoebe_nav2_config, "config/", slam_config_file]),
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
        # Use custom nav launch file for tf prefixing fix
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [PathJoinSubstitution([(pkg_phoebe_nav2_config), "launch", "navigation_launch.py"])]
            ),
            launch_arguments={
                "namespace": "",
                "tf_prefix": tf_prefix,
                "params_file": PathJoinSubstitution([pkg_phoebe_nav2_config, "config", nav2_config_file]),
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
                "localization_config": localization_config,
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
        ),
        # Launch the odom to joint state publisher if not using tf from sensors/slam
        Node(
            package="phoebe_deploy",
            executable="odometry_joint_state_publisher.py",
            name="odometry_joint_state_publisher",
            parameters=[{"use_sim_time": use_sim_time}],
            condition=UnlessCondition(publish_tf),
        ),
        Node(
            package="twist_mux",
            executable="twist_mux",
            namespace="",
            output="both",
            remappings={
                ("cmd_vel_out", reference_topic),
                ("/diagnostics", "diagnostics"),
            },
            parameters=[
                ParameterFile(config_twist_mux, allow_substs=True),
                {"use_sim_time": use_sim_time},
            ],
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
