#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.parameter_descriptions import ParameterFile


def generate_launch_description():

    declared_arguments = []

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
            "ns",
            default_value="",
            description="Namespace for the hardware robot",
        )
    )

    # Initialize Arguments
    ns = LaunchConfiguration("ns")

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
            ],
            output="screen",
        )

    # helper function to get controllers files that we might need
    def GetControllersFile(file_name):
        return PathJoinSubstitution(
            [
                get_package_share_directory("phoebe_deploy"),
                "config",
                file_name,
            ]
        )

    # launch controller manager

    # contains update rate
    controllers_common = GetControllersFile("controllers_common.yaml")
    # controllers for the ridgeback
    controllers_r100 = GetControllersFile("controllers_r100.yaml")

    nodes = []

    # start the controller manager node with all of the controller config files
    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        namespace=ns,
        # allow_substs allows tf_prefix to be pulled in
        parameters=[
            ParameterFile(controllers_common, allow_substs=True),
            ParameterFile(controllers_r100, allow_substs=True),
        ],
        remappings=[
            # remap to be able to use the global robot_description
            ("~/robot_description", "robot_description"),
            # Necessary remap for platform velocity controller. Preferably this would be done
            # at spawn time. This is not supported in humble, but is supported in jazzy.
        ],
        output="both",
    )

    node_puma_throttle = Node(
        name="puma_throttle",
        executable="throttle",
        package="topic_tools",
        namespace=ns,
        output="screen",
        arguments=["messages", "platform/puma/cmd", "50", "ridgeback/platform/puma/cmd_throttle"],
    )

    platform_velocity_controller = MakeControllerNode("platform_velocity_controller")
    joint_state_broadcaster = MakeControllerNode("joint_state_broadcaster")

    nodes = [control_node, node_puma_throttle, platform_velocity_controller, joint_state_broadcaster]

    ns_action = GroupAction(actions=[PushRosNamespace(ns)] + nodes)

    return LaunchDescription(declared_arguments + [ns_action])
