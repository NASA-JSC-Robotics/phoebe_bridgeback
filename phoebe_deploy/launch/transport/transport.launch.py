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
