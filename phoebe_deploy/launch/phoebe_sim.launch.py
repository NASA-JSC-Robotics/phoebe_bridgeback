#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

    
def generate_launch_description():
    
    controller_manager_name = '/controller_manager'
    
    arg_tf_prefix = DeclareLaunchArgument(
        "tf_prefix",
        default_value='""',
        description="tf_prefix of the joint names, useful for \
        multi-robot setup. If changed, also joint names in the controllers' configuration \
        have to be updated.",
        
    )
    arg_use_fake_hardware = DeclareLaunchArgument(
        "use_fake_hardware",
        default_value="true",
        description="Start robot with fake hardware mirroring command to its states.",
    )
    arg_headless_mode = DeclareLaunchArgument(
        "headless_mode",
        default_value="false",
        description="Enable headless mode for robot control",
    )
    pkg_deploy = get_package_share_directory('phoebe_deploy')
    pkg_description = get_package_share_directory('phoebe_description')
    
    robot_controllers = PathJoinSubstitution(
        [
            FindPackageShare("phoebe_deploy"),
            "config",
            "config.yaml",
        ]
    )
    urdf_model_path = os.path.join(pkg_description, 'urdf/phoebe.urdf.xacro')
    
    # Initialize Arguments
    tf_prefix = LaunchConfiguration("tf_prefix")
    use_fake_hardware = LaunchConfiguration("use_fake_hardware")
    headless_mode = LaunchConfiguration("headless_mode")
    namespace = LaunchConfiguration("namespace")

    pkg_deploy = get_package_share_directory('phoebe_deploy')
    pkg_description = get_package_share_directory('phoebe_description')
    
    # Start gazebo with the selected World
    start_world = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_deploy, 'launch', 'start_world.launch.py')
        )
    )

    # add the robot to the world
    spawn_robot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_description, 'launch', 'spawn_robot.launch.py')),
        launch_arguments = {
            'use_sim_time' : use_fake_hardware,
#            'namespace' : namespace
        }.items()
    )
    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        name="joint_state_broadcaster_control",
        parameters=[urdf_model_path, robot_controllers],
        arguments=[
            'joint_state_broadcaster',
            '--controller-manager-timeout',
            '300',
            '-c',
            controller_manager_name,
        ],
        additional_env={'ROS_SUPER_CLIENT': 'True'},
    )

    # Add Platform Velocity Controller
    velocity_controller = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['platform_velocity_controller', 
                   '--controller-manager-timeout', '300',
                   '-c',
                   controller_manager_name,
                   ],
#        remappings=REMAPPINGS,
        output='screen',
        additional_env={'ROS_SUPER_CLIENT': 'True'},
    )
    
    return LaunchDescription([
        arg_tf_prefix,
        arg_use_fake_hardware,
        arg_headless_mode,
        start_world,
        spawn_robot,
        joint_state_broadcaster,
        velocity_controller
    ])