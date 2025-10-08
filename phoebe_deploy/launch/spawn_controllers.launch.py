#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, ExecuteProcess, RegisterEventHandler
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.conditions import IfCondition, UnlessCondition
from ament_index_python.packages import get_package_share_directory
from launch_ros.substitutions import FindPackagePrefix
from launch.event_handlers import OnProcessExit


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

    tf_prefix = LaunchConfiguration("tf_prefix")
    ns = LaunchConfiguration("ns")
    calibration_mode = LaunchConfiguration("calibration_mode")

    # common launch args passed to each of the different launch files
    common_launch_args = {
        "tf_prefix": tf_prefix,
        "ns": ns,
    }.items()

    # helper function to organize launch description objects with the same launch args and package names
    def MakeLaunchDescription(launch_file, launch_args, condition=IfCondition("true")):
        return IncludeLaunchDescription(
            PythonLaunchDescriptionSource(launch_file),
            launch_arguments=launch_args,
            condition=condition,
        )

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

    joint_state_broadcaster = MakeControllerNode("joint_state_broadcaster")

    launches = []

    pkg_phoebe_deploy = get_package_share_directory("phoebe_deploy")

    # add controller spawner launch files for each individual subsystem
    launch_file_r100_spawner = PathJoinSubstitution(
        [pkg_phoebe_deploy, "launch", "spawn_controllers", "spawn_controllers_r100.launch.py"]
    )
    launch_file_ewellix_spawner = PathJoinSubstitution(
        [pkg_phoebe_deploy, "launch", "spawn_controllers", "spawn_controllers_ewellix.launch.py"]
    )
    launch_file_ur_spawner = PathJoinSubstitution(
        [pkg_phoebe_deploy, "launch", "spawn_controllers", "spawn_controllers_ur.launch.py"]
    )
    launch_file_hande_spawner = PathJoinSubstitution(
        [pkg_phoebe_deploy, "launch", "spawn_controllers", "spawn_controllers_hande.launch.py"]
    )

    # Thread prioritization should happen, clearly, after the threads have been started.
    # The threads of interest are the controller manager main thread and control loop thread.
    # Create a process to do the prioritization, then we will tie it to the exit of a spawner
    # node that adds a controller to controller manager. This should ensure that controller
    # manager itself has had time to initialize and start processing controllers.
    prioritize_threads = ExecuteProcess(
        shell=True,
        cmd=[
            PathJoinSubstitution([FindPackagePrefix("phoebe_deploy"), "lib", "phoebe_deploy", "prioritize_threads.sh"])
        ],
        output="both",
    )

    launches.append(MakeLaunchDescription(launch_file_r100_spawner, common_launch_args))
    launches.append(MakeLaunchDescription(launch_file_ewellix_spawner, common_launch_args))
    launches.append(MakeLaunchDescription(launch_file_ur_spawner, common_launch_args))
    launches.append(
        MakeLaunchDescription(
            launch_file_hande_spawner, common_launch_args, condition=UnlessCondition(calibration_mode)
        )
    )

    return LaunchDescription(
        declared_arguments
        + launches
        + [joint_state_broadcaster]
        + [RegisterEventHandler(OnProcessExit(target_action=joint_state_broadcaster, on_exit=[prioritize_threads]))]
    )
