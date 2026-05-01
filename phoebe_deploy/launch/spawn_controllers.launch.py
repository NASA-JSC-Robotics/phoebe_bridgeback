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
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    ExecuteProcess,
    RegisterEventHandler,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.conditions import IfCondition, UnlessCondition
from ament_index_python.packages import get_package_share_directory
from launch_ros.substitutions import FindPackagePrefix
from launch.event_handlers import OnProcessExit

from phoebe_deploy.launch_helpers import spawn_controller


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
    declared_arguments.append(
        DeclareLaunchArgument(
            "calibration_mode",
            default_value="false",
            description="Whether or not we are running the calibration routine",
            choices=["true", "false"],
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "is_sim",
            default_value="false",
            description="This is some kind of simulation environment",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_left_static_pedestal",
            default_value="false",
            description="Replaces the left liftkit with the static pedestal",
        )
    )

    tf_prefix = LaunchConfiguration("tf_prefix")
    ns = LaunchConfiguration("ns")
    calibration_mode = LaunchConfiguration("calibration_mode")
    is_sim = LaunchConfiguration("is_sim")
    use_left_static_pedestal = LaunchConfiguration("use_left_static_pedestal")

    # common launch args passed to each of the different launch files
    common_launch_args = {
        "tf_prefix": tf_prefix,
        "ns": ns,
        "calibration_mode": calibration_mode,
        "is_sim": is_sim,
        "use_left_static_pedestal": use_left_static_pedestal,
    }.items()

    # helper function to organize launch description objects with the same launch args and package names
    def MakeLaunchDescription(launch_file, launch_args, condition=IfCondition("true")):
        return IncludeLaunchDescription(
            PythonLaunchDescriptionSource(launch_file),
            launch_arguments=launch_args,
            condition=condition,
        )

    joint_state_broadcaster = spawn_controller("joint_state_broadcaster")

    launches = []

    pkg_phoebe_deploy = get_package_share_directory("phoebe_deploy")

    # add controller spawner launch files for each individual subsystem
    launch_file_r100_spawner = PathJoinSubstitution(
        [
            pkg_phoebe_deploy,
            "launch",
            "spawn_controllers",
            "spawn_controllers_r100.launch.py",
        ]
    )
    launch_file_ewellix_spawner = PathJoinSubstitution(
        [
            pkg_phoebe_deploy,
            "launch",
            "spawn_controllers",
            "spawn_controllers_ewellix.launch.py",
        ]
    )
    launch_file_ur_spawner = PathJoinSubstitution(
        [
            pkg_phoebe_deploy,
            "launch",
            "spawn_controllers",
            "spawn_controllers_ur.launch.py",
        ]
    )
    launch_file_hande_spawner = PathJoinSubstitution(
        [
            pkg_phoebe_deploy,
            "launch",
            "spawn_controllers",
            "spawn_controllers_hande.launch.py",
        ]
    )

    # Thread prioritization should happen, clearly, after the threads have been started.
    # The threads of interest are the controller manager main thread and control loop thread.
    # Create a process to do the prioritization, then we will tie it to the exit of a spawner
    # node that adds a controller to controller manager. This should ensure that controller
    # manager itself has had time to initialize and start processing controllers.
    prioritize_threads = ExecuteProcess(
        shell=True,
        cmd=[
            PathJoinSubstitution(
                [
                    FindPackagePrefix("phoebe_deploy"),
                    "lib",
                    "phoebe_deploy",
                    "prioritize_threads.sh",
                ]
            )
        ],
        # condition=UnlessCondition(is_sim),
    )

    launches.append(MakeLaunchDescription(launch_file_r100_spawner, common_launch_args))
    launches.append(
        MakeLaunchDescription(
            launch_file_ewellix_spawner,
            common_launch_args,
        )
    )
    launches.append(MakeLaunchDescription(launch_file_ur_spawner, common_launch_args))
    launches.append(
        MakeLaunchDescription(
            launch_file_hande_spawner,
            common_launch_args,
            condition=UnlessCondition(calibration_mode),
        )
    )

    return LaunchDescription(
        declared_arguments
        + launches
        + [joint_state_broadcaster]
        + [RegisterEventHandler(OnProcessExit(target_action=joint_state_broadcaster, on_exit=[prioritize_threads]))]
    )
