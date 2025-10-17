#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import (
    LaunchConfiguration,
)
from launch_ros.actions import Node
from launch.conditions import UnlessCondition


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

    nodes.append(MakeControllerNode("right_io_and_status_controller", condition=UnlessCondition(is_sim)))
    nodes.append(MakeControllerNode("right_force_torque_sensor_broadcaster"))
    nodes.append(MakeControllerNode("right_ur_joint_trajectory_controller"))
    nodes.append(MakeControllerNode("right_freedrive_mode_controller", active=False, condition=UnlessCondition(is_sim)))
    nodes.append(MakeControllerNode("left_io_and_status_controller", condition=UnlessCondition(is_sim)))
    nodes.append(MakeControllerNode("left_force_torque_sensor_broadcaster"))
    nodes.append(MakeControllerNode("left_ur_joint_trajectory_controller"))
    nodes.append(MakeControllerNode("left_freedrive_mode_controller", active=False, condition=UnlessCondition(is_sim)))

    return LaunchDescription(declared_arguments + nodes)
