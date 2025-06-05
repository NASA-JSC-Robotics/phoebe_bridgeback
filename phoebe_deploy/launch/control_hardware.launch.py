#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    LaunchConfiguration,
)
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import PushRosNamespace


def generate_launch_description():

    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "ns",
            default_value="",
            description="Namespace for the hardware robot",
        )
    )

    # Initialize Arguments
    ns = LaunchConfiguration("ns")

    control_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory("phoebe_deploy"), "launch", "control.launch.py")
        ),
        launch_arguments={
            "use_fake_hardware": "false",
            "sim_ignition": "false",
            "ns": ns,
        }.items(),
    )

    ns_action = GroupAction(actions=[PushRosNamespace(ns)] + [control_launch])

    return LaunchDescription(declared_arguments + [ns_action])
