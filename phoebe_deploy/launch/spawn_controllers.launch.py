#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    LaunchConfiguration,
)
from ament_index_python.packages import get_package_share_directory


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

    tf_prefix = LaunchConfiguration("tf_prefix")
    ns = LaunchConfiguration("ns")

    # common launch args passed to each of the different launch files
    common_launch_args = {
        "tf_prefix": tf_prefix,
        "ns": ns,
    }.items()

    launch_file_names = []

    # helper function to organize launch description objects with the same launch args and package names
    def AddLaunchDescriptions(package_name, launch_file_names, launch_args):
        launch_files_list = []
        for launch_file_name in launch_file_names:
            launch_files_list.append(
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        os.path.join(get_package_share_directory(package_name), "launch", launch_file_name)
                    ),
                    launch_arguments=launch_args,
                )
            )

        return launch_files_list

    # helper function to make controller nodes
    def MakeControllerNode(controller_name):
        return Node(
            package="controller_manager",
            executable="spawner",
            name=controller_name,
            arguments=[
                "--controller-manager",
                "controller_namager",
                "--controller-manager-timeout",
                "300",
                "--namespace",
                ns,
                controller_name,
            ],
            output="screen",
        )

    joint_state_broadcaster = MakeControllerNode("joint_state_broadcaster")

    # add controller spawner launch files for each individual subsystem
    launch_file_names.append("spawn_controllers/spawn_controllers_r100.launch.py")
    launch_file_names.append("spawn_controllers/spawn_controllers_ewellix.launch.py")
    launch_file_names.append("spawn_controllers/spawn_controllers_ur.launch.py")
    launch_file_names.append("spawn_controllers/spawn_controllers_hande.launch.py")

    launch_files = AddLaunchDescriptions(
        package_name="phoebe_deploy", launch_file_names=launch_file_names, launch_args=common_launch_args
    )

    return LaunchDescription(declared_arguments + launch_files + [joint_state_broadcaster])
