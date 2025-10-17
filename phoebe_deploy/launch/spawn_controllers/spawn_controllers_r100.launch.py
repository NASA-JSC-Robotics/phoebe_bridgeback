#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import (
    LaunchConfiguration,
)
from launch_ros.actions import Node
from launch.conditions import IfCondition


def generate_launch_description():

    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "ns",
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

    ns = LaunchConfiguration("ns")
    is_sim = LaunchConfiguration("is_sim")

    nodes = []

    # helper function to make controller nodes
    def MakeControllerNode(controller_name, active=True, condition=None):
        arguments = [
            "--controller-manager",
            "controller_manager",
            "--controller-manager-timeout",
            "300",
            "--namespace",
            ns,
            controller_name,
        ]
        if not active:
            arguments.append("--inactive")

        return Node(
            package="controller_manager",
            executable="spawner",
            name=controller_name,
            arguments=arguments,
            output="screen",
            condition=condition,
        )

    nodes.append(MakeControllerNode("platform_velocity_controller"))
    nodes.append(MakeControllerNode("odom_publisher"))
    nodes.append(
        MakeControllerNode(
            "imu_broadcaster",
            condition=IfCondition(is_sim),
        )
    )

    return LaunchDescription(declared_arguments + nodes)
