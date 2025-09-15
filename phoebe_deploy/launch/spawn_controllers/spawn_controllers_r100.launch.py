#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import (
    LaunchConfiguration,
)
from launch_ros.actions import Node


def generate_launch_description():

    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "ns",
            default_value="",
            description="Namespace for the hardware robot",
        )
    )

    ns = LaunchConfiguration("ns")

    nodes = []

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
                ns,
                controller_name,
                # The following works in rolling, but not in humble. For humble, the only way to remap
                # topics used by a controller is to remap them for the entire controller_manager.
                # "--controller-ros-args",
                # "--ros-args",
                # "--remapping",
                # "~/cmd_vel_unstamped:=/platform/cmd_vel_unstamped",
            ],
            output="screen",
        )

    nodes.append(MakeControllerNode("platform_velocity_controller"))
    nodes.append(MakeControllerNode("odom_publisher"))

    return LaunchDescription(declared_arguments + nodes)
