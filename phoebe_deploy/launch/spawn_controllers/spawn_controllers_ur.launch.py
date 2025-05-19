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
    def MakeControllerNode(controller_name, active = True):
        arguments=[
                "--controller-manager",
                "controller_manager",
                "--controller-manager-timeout",
                "300",
                "--namespace",
                ns,
                controller_name,
            ]
        if not active: arguments.append("--inactive")
        
        return Node(
            package="controller_manager",
            executable="spawner",
            name=controller_name,
            arguments=arguments,
            output="screen",
        )

    nodes.append(MakeControllerNode("right_io_and_status_controller"))
    nodes.append(MakeControllerNode("right_force_torque_sensor_broadcaster"))
    nodes.append(MakeControllerNode("right_ur_joint_trajectory_controller"))
    nodes.append(MakeControllerNode("right_freedrive_mode_controller",active=False))
    nodes.append(MakeControllerNode("left_io_and_status_controller"))
    nodes.append(MakeControllerNode("left_force_torque_sensor_broadcaster"))
    nodes.append(MakeControllerNode("left_ur_joint_trajectory_controller"))
    nodes.append(MakeControllerNode("left_freedrive_mode_controller",active=False))

    return LaunchDescription(declared_arguments + nodes)
