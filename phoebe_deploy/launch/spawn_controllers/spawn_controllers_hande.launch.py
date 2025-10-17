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
    def MakeControllerNode(controller_name, condition=None):
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
            ],
            output="screen",
            condition=condition,
        )

    # need to fix name conflict by adding parameters before the activation controllers
    # can be added back in.
    nodes.append(MakeControllerNode("right_robotiq_gripper_hande_controller"))
    nodes.append(MakeControllerNode("right_robotiq_activation_controller", condition=UnlessCondition(is_sim)))
    nodes.append(MakeControllerNode("left_robotiq_gripper_hande_controller"))
    nodes.append(MakeControllerNode("left_robotiq_activation_controller", condition=UnlessCondition(is_sim)))

    return LaunchDescription(declared_arguments + nodes)
