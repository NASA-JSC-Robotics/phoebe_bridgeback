#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterFile
from launch.conditions import IfCondition


def launch_setup(context, *args, **kwargs):

    # Initialize Arguments
    platform = LaunchConfiguration("platform")
    tf_prefix = LaunchConfiguration("tf_prefix")
    ns = LaunchConfiguration("ns")

    # convert platform type to string so that we can evaluate different options
    platform_string = platform.perform(context)
    sim_ignition = "true" if platform_string == "sim_ignition" else "false"
    use_fake_hardware = "true" if platform_string == "mock_hardware" else "false"
    hardware = "true" if platform_string == "hardware" else "false"

    # common launch args shared across different nodes
    common_launch_args = {
        "sim_ignition": sim_ignition,
        "use_fake_hardware": use_fake_hardware,
        "tf_prefix": tf_prefix,
        "ns": ns,
    }.items()

    # helper function to organize launch description objects with the same launch args and package names
    def AddLaunchDescriptions(package_name, launch_file_names, launch_args, if_condition="true"):
        launch_files_list = []
        for launch_file_name in launch_file_names:
            launch_files_list.append(
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        os.path.join(get_package_share_directory(package_name), "launch", launch_file_name)
                    ),
                    launch_arguments=launch_args,
                    condition=IfCondition(if_condition),
                )
            )

        return launch_files_list

    # lists to keep track of launch file names to start
    launch_file_names = []
    hardware_launch_file_names = []

    # This is the "definitive" robot state publisher.
    # This should be launched on whatever machine has the most resources, which
    # along with whichever controller manager we think should com up first.
    launch_file_names.append("robot_state_publisher.launch.py")

    # add controller spawners for each component
    launch_file_names.append("spawn_controllers.launch.py")

    # add launch file for handling tool communication for hande through the URs
    hardware_launch_file_names.append("hande_tool_comm.launch.py")

    # generate the launch files based on launch_file_names which has been configured
    launch_files = AddLaunchDescriptions(
        package_name="phoebe_deploy",
        launch_file_names=launch_file_names,
        launch_args=common_launch_args,
    )

    # generate the hardware only launch files based on hardware_launch_file_names
    hardware_launch_files = AddLaunchDescriptions(
        package_name="phoebe_deploy",
        launch_file_names=hardware_launch_file_names,
        launch_args=common_launch_args,
        if_condition=hardware,
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
    # controllers for the liftkits
    controllers_ewellix = GetControllersFile("controllers_ewellix.yaml")
    # controllers for the urs
    controllers_ur = GetControllersFile("controllers_ur.yaml")
    # controllers for the grippers
    controllers_hande = GetControllersFile("controllers_hande.yaml")

    # start the controller manager node with all of the controller config files
    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        namespace=ns,
        # allow_substs allows tf_prefix to be pulled in
        parameters=[
            ParameterFile(controllers_common, allow_substs=True),
            ParameterFile(controllers_r100, allow_substs=True),
            ParameterFile(controllers_ewellix, allow_substs=True),
            ParameterFile(controllers_ur, allow_substs=True),
            ParameterFile(controllers_hande, allow_substs=True),
        ],
        
        remappings=[
            # remap to be able to use the global robot_description
            ("~/robot_description", "robot_description"),
            # Necessary remap for platform velocity controller. Preferably this would be done
            # at spawn time. This is not supported in humble, but is supported in jazzy.
            ("/platform_velocity_controller/cmd_vel_unstamped", "/platform/cmd_vel_unstamped")
        ],
        output="both",
    )

    return launch_files + [control_node]


def generate_launch_description():

    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "platform",
            default_value="hardware",
            description="Whether to run the robot on hardware, mock_hardware, or sim_ignition.",
            choices=["hardware", "mock_hardware", "sim_ignition"],
        )
    )
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

    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])
