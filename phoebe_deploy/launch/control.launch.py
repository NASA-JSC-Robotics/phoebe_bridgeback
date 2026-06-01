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
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node
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
            "namespace",
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
    declared_arguments.append(
        DeclareLaunchArgument(
            "left_hand_type",
            default_value="hande",
            choices=["hande", "2f85"],
            description="Hand type to put on the left arm of phoebe",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "right_hand_type",
            default_value="hande",
            choices=["hande", "2f85"],
            description="Hand type to put on the right arm of phoebe",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "extra_xacro_args",
            default_value="",
            description="Extra args to add for making a robot description. "
            "Should be in the format of 'arg1:=value1 arg2:=value2'",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "extra_controller_params_file",
            default_value=PathJoinSubstitution(
                [FindPackageShare("phoebe_deploy"), "config", "empty_config.yaml"]
            ),
            description="Path to additional parameter file to be loaded into the control node.",
        )
    )

    # Initialize Arguments
    use_fake_hardware = LaunchConfiguration("use_fake_hardware")
    use_sim_time = LaunchConfiguration("use_sim_time")
    tf_prefix = LaunchConfiguration("tf_prefix")
    namespace = LaunchConfiguration("namespace")
    calibration_mode = LaunchConfiguration("calibration_mode")
    robot_description_package = LaunchConfiguration("robot_description_package")
    robot_description_file = LaunchConfiguration("robot_description_file")
    include_world_joints = LaunchConfiguration("include_world_joints")
    use_left_static_pedestal = LaunchConfiguration("use_left_static_pedestal")
    left_hand_type = LaunchConfiguration("left_hand_type")
    right_hand_type = LaunchConfiguration("right_hand_type")
    extra_xacro_args = LaunchConfiguration("extra_xacro_args")
    extra_controller_params_file = LaunchConfiguration("extra_controller_params_file")

    # common launch args shared across different nodes
    common_launch_args = {
        "use_fake_hardware": use_fake_hardware,
        "tf_prefix": tf_prefix,
        "namespace": namespace,
        "calibration_mode": calibration_mode,
        "robot_description_package": robot_description_package,
        "robot_description_file": robot_description_file,
        "is_sim": use_fake_hardware,
        "include_world_joints": include_world_joints,
        "use_left_static_pedestal": use_left_static_pedestal,
        "left_hand_type": left_hand_type,
        "right_hand_type": right_hand_type,
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
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution([FindPackageShare(robot_description_package), "urdf", robot_description_file]),
            " ",
            "ns:=",
            namespace,
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
            "left_hand_type:=",
            left_hand_type,
            " ",
            "right_hand_type:=",
            right_hand_type,
            " ",
            extra_xacro_args,  # this should always be last
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
        namespace=namespace,
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
        namespace=namespace,
        # allow_substs allows tf_prefix to be pulled in
        parameters=[
            ParameterFile(controllers_common, allow_substs=True),
            ParameterFile(controllers_r100, allow_substs=True),
            ParameterFile(controllers_ewellix, allow_substs=True),
            ParameterFile(controllers_ur, allow_substs=True),
            ParameterFile(controllers_hande, allow_substs=True),
            ParameterFile(controllers_moveit_pro, allow_substs=True),
            ParameterFile(extra_controller_params_file, allow_substs=True),
            {"use_sim_time": use_sim_time},
        ],
        remappings=[
            # This is throwing a deprecation warning, as ros2_control would
            # prefer to have this tied to a controller, not the controller
            # manager, but there is no controller for this to go to unfortunately
            # when this is running in mujoco.
            ("/lidar2d_0_laser/scan", "/ridgeback/sensors/lidar2d_0/scan"),
        ],
        output="both",
        arguments=["--ros-args", "--log-level", "info"],
    )

    node_puma_throttle = Node(
        name="puma_throttle",
        executable="throttle",
        package="topic_tools",
        namespace=namespace,
        output="screen",
        arguments=[
            "messages",
            "platform/puma/cmd",
            "50",
            "ridgeback/platform/puma/cmd_throttle",
        ],
        condition=UnlessCondition(use_fake_hardware),
    )

    return LaunchDescription(
        declared_arguments + launch_files + [robot_state_publisher_node, control_node, node_puma_throttle]
    )
