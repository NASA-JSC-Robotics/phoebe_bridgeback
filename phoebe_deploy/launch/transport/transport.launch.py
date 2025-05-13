#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.conditions import IfCondition
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration
from launch_ros.substitutions import FindPackageShare


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

    common_launch_args = {
        "tf_prefix": tf_prefix,
        "ns": ns,
    }.items()

    # Include Packages
    pkg_phoebe_deploy = FindPackageShare("phoebe_deploy")

    # helper function to organize launch description objects with the same launch args and package names
    def MakeLaunchDescription(launch_file, launch_args, if_condition="true"):
        return IncludeLaunchDescription(
            PythonLaunchDescriptionSource(launch_file),
            launch_arguments=launch_args,
            condition=IfCondition(if_condition),
        )

    launches = []

    launch_file_transport_control = PathJoinSubstitution(
        [pkg_phoebe_deploy, "launch", "transport", "transport_control.launch.py"]
    )
    launch_file_transport_rsp = PathJoinSubstitution(
        [pkg_phoebe_deploy, "launch", "transport", "transport_robot_state_publisher.launch.py"]
    )
    launch_file_ridgeback_comm = PathJoinSubstitution([pkg_phoebe_deploy, "launch", "ridgeback_comm.launch.py"])
    launch_file_teleop = PathJoinSubstitution([pkg_phoebe_deploy, "launch", "teleop.launch.py"])

    launches.append(MakeLaunchDescription(launch_file_transport_control, common_launch_args))
    launches.append(MakeLaunchDescription(launch_file_transport_rsp, common_launch_args))
    launches.append(MakeLaunchDescription(launch_file_teleop, common_launch_args))
    launches.append(MakeLaunchDescription(launch_file_ridgeback_comm, common_launch_args))

    return LaunchDescription(declared_arguments + launches)
