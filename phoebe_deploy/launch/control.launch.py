#!/usr/bin/env python3


import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, OpaqueFunction
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    
    namespace = LaunchConfiguration("namespace")
    
    pkg_description = get_package_share_directory('phoebe_description')
    
    robot_controllers = PathJoinSubstitution(
        [
            FindPackageShare("phoebe_deploy"),
            "config",
            "control.yaml",
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
        ],
        additional_env={'ROS_SUPER_CLIENT': 'True'},
    )

    # Add Platform Velocity Controller
    velocity_controller = Node(
        package='controller_manager',
        executable='spawner',
        name="velocity_controller",
        arguments=['velocity_controller', 
                   '--controller-manager-timeout', '300',
                   ],
        output='screen',
        additional_env={'ROS_SUPER_CLIENT': 'True'},
    )

    ld = LaunchDescription()
    ld.add_action(joint_state_broadcaster)
    ld.add_action(velocity_controller)
    return ld
