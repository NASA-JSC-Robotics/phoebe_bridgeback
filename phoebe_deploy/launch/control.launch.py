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


import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.parameter_descriptions import ParameterFile
from launch.conditions import IfCondition, UnlessCondition
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():

    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "use_fake_hardware",
            default_value="false",
            description="Start robot with simulated hardware mirroring command to its states.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="false",
            description="If the robot is running in simulation, use the published clock",
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
            "robot_description_package",
            default_value="phoebe_description",
            description="The package to find the robot description.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "robot_description_file",
            default_value="phoebe.urdf.xacro",
            description="The name of the robot description file. "
            "Must be in the 'urdf' folder of the description package.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "include_world_joints",
            default_value="false",
            description="Whether or not to include a root world frame",
            choices=["true", "false"],
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_left_static_pedestal",
            default_value="false",
            description="Replaces the left liftkit with the static pedestal",
        )
    )

    # Initialize Arguments
    use_fake_hardware = LaunchConfiguration("use_fake_hardware")
    use_sim_time = LaunchConfiguration("use_sim_time")
    tf_prefix = LaunchConfiguration("tf_prefix")
    ns = LaunchConfiguration("ns")
    calibration_mode = LaunchConfiguration("calibration_mode")
    robot_description_package = LaunchConfiguration("robot_description_package")
    robot_description_file = LaunchConfiguration("robot_description_file")
    include_world_joints = LaunchConfiguration("include_world_joints")
    use_left_static_pedestal = LaunchConfiguration("use_left_static_pedestal")

    # common launch args shared across different nodes
    common_launch_args = {
        "use_fake_hardware": use_fake_hardware,
        "tf_prefix": tf_prefix,
        "ns": ns,
        "calibration_mode": calibration_mode,
        "robot_description_package": robot_description_package,
        "robot_description_file": robot_description_file,
        "is_sim": use_fake_hardware,
        "include_world_joints": include_world_joints,
        "use_left_static_pedestal": use_left_static_pedestal,
    }.items()

    # helper function to organize launch description objects with the same launch args and package names
    def AddLaunchDescriptions(package_name, launch_file_names, launch_args, if_condition="true"):
        launch_files_list = []
        for launch_file_name in launch_file_names:
            launch_files_list.append(
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        os.path.join(
                            get_package_share_directory(package_name),
                            "launch",
                            launch_file_name,
                        )
                    ),
                    launch_arguments=launch_args,
                    condition=IfCondition(if_condition),
                )
            )

        return launch_files_list

    # lists to keep track of launch file names to start
    launch_file_names = []
    hardware_launch_file_names = []

    # add controller spawners for each component
    launch_file_names.append("spawn_controllers.launch.py")

    # add launch file for handling tool communication for gripper through the URs
    hardware_launch_file_names.append("hande_tool_comm.launch.py")

    # generate the launch files based on launch_file_names which has been configured
    launch_files = AddLaunchDescriptions(
        package_name="phoebe_deploy",
        launch_file_names=launch_file_names,
        launch_args=common_launch_args,
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
    # controllers for moveit pro (must be spawned separately)
    controllers_moveit_pro = GetControllersFile("controllers_moveit_pro.yaml")

    # This is the main robot description for Phoebe.
    # Unfortunately, we need the robot description for the controller manager to launch admittance controllers.
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution([FindPackageShare(robot_description_package), "urdf", robot_description_file]),
            " ",
            "ns:=",
            ns,
            " ",
            "tf_prefix:=",
            tf_prefix,
            " ",
            "use_fake_hardware:=",
            use_fake_hardware,
            " ",
            "include_world_joints:=",
            include_world_joints,
            " ",
            "calibration_mode:=",
            calibration_mode,
            " ",
            "use_left_static_pedestal:=",
            use_left_static_pedestal,
            " ",
        ]
    )
    robot_description = {"robot_description": ParameterValue(value=robot_description_content, value_type=str)}

    # This is the "definitive" robot state publisher.
    # This should be launched on whatever machine has the most resources, which
    # along with whichever controller manager we think should com up first.
    # Note that this is distinct from when running in transport only mode!
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        namespace=ns,
        output="both",
        parameters=[
            robot_description,
            {"use_sim_time": use_sim_time},
        ],
    )

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
            ParameterFile(controllers_moveit_pro, allow_substs=True),
            {"use_sim_time": use_sim_time},
            robot_description,
        ],
        remappings=[
            # remap to be able to use the global robot_description
            ("~/robot_description", "robot_description"),
            # Necessary remap for platform velocity controller. Preferably this would be done
            # at spawn time. This is not supported in humble, but is supported in jazzy.
            ("/imu_broadcaster/imu", "/ridgeback/sensors/imu_0/data_raw"),
            ("/lidar2d_0_laser/scan", "/ridgeback/sensors/lidar2d_0/scan"),
        ],
        output="both",
        condition=UnlessCondition(use_fake_hardware),
    )

    # start the controller manager node with all of the controller config files
    # this is the version for sim, which just sets the kinematics.wheel radius to a smaller value for mujoco
    control_node_sim = Node(
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
            ParameterFile(controllers_moveit_pro, allow_substs=True),
            robot_description,
            # for some reason, in sim, we have to set the wheel radius to ~0.063 for it to behave realistically
            {
                "use_sim_time": use_sim_time,
                "kinematics.wheels_radius": 0.063,
            },
        ],
        remappings=[
            # remap to be able to use the global robot_description
            ("~/robot_description", "robot_description"),
            # Necessary remap for platform velocity controller. Preferably this would be done
            # at spawn time. This is not supported in humble, but is supported in jazzy.
            ("/imu_broadcaster/imu", "/ridgeback/sensors/imu_0/data_raw"),
            ("/lidar2d_0_laser/scan", "/ridgeback/sensors/lidar2d_0/scan"),
        ],
        output="both",
        condition=IfCondition(use_fake_hardware),
    )

    node_puma_throttle = Node(
        name="puma_throttle",
        executable="throttle",
        package="topic_tools",
        namespace=ns,
        output="screen",
        arguments=[
            "messages",
            "platform/puma/cmd",
            "50",
            "ridgeback/platform/puma/cmd_throttle",
        ],
        condition=UnlessCondition(use_fake_hardware),
    )

    ns_action = GroupAction(
        actions=[PushRosNamespace(ns)]
        + launch_files
        + [robot_state_publisher_node, control_node, control_node_sim, node_puma_throttle]
    )

    return LaunchDescription(declared_arguments + [ns_action])
