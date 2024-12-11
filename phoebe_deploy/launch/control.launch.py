#!/usr/bin/env python3


import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, OpaqueFunction
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory

REMAPPINGS = [
    ('joint_states', 'platform/joint_states'),
    ('dynamic_joint_states', 'platform/dynamic_joint_states'),
    ('platform_velocity_controller/odom', 'platform/odom'),
    ('platform_velocity_controller/cmd_vel_unstamped', 'platform/cmd_vel_unstamped'),
    ('platform_velocity_controller/reference', 'platform/cmd_vel_unstamped'),
    ('/diagnostics', 'diagnostics'),
    ('/tf', 'tf'),
    ('/tf_static', 'tf_static'),
    ('~/robot_description', 'robot_description'),
]

controller_manager_name = '/controller_manager'

def generate_launch_description():
    
    pkg_description = get_package_share_directory('phoebe_description')
    
    robot_controllers = PathJoinSubstitution(
        [
            FindPackageShare("phoebe_deploy"),
            "config",
            "config.yaml",
        ]
    )
    urdf_model_path = os.path.join(pkg_description, 'urdf/phoebe.urdf.xacro')
    
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
    platform_velocity_controller = Node(
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

    ld = LaunchDescription()
    ld.add_action(joint_state_broadcaster)
    ld.add_action(platform_velocity_controller)
    return ld
