#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os

from ament_index_python.packages import get_package_share_directory

import launch
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node


def generate_launch_description():
    
    namespace = launch.substitutions.LaunchConfiguration("ns")
    
    arguments = []
    
    arguments.append(DeclareLaunchArgument(
        "ns",
        default_value="robot",
    ))
    
    joy_config = launch.substitutions.LaunchConfiguration('joy_config')
    joy_dev = launch.substitutions.LaunchConfiguration('joy_dev')
    publish_stamped_twist = launch.substitutions.LaunchConfiguration('publish_stamped_twist')
    config_filepath = launch.substitutions.LaunchConfiguration('config_filepath')

    arguments.append(DeclareLaunchArgument('joy_vel', default_value='cmd_vel_unstamped'))
    arguments.append(DeclareLaunchArgument('joy_config', default_value='joy_config'))
    arguments.append(DeclareLaunchArgument('joy_dev', default_value='0'))
    arguments.append(DeclareLaunchArgument('publish_stamped_twist', default_value='false'))
    
    arguments.append(DeclareLaunchArgument('config_filepath', default_value=[
            launch.substitutions.TextSubstitution(text=os.path.join(
                get_package_share_directory('phoebe_deploy'), 'config', '')),
            joy_config, launch.substitutions.TextSubstitution(text='.yaml')]))
    
    
    joy = Node(
        package='joy', 
        executable='joy_node', 
        name='joy_node',
        namespace=namespace,
        parameters=[{
            'joy_dev': joy_dev,
            'deadzone': 0.3,
            'autorepeat_rate': 20.0,
            'use_sim_time': True,
        }],
        remappings=[
            ('/diagnostics', 'diagnostics'),
            ('/tf', 'tf'),
            ('/tf_static', 'tf_static'),
            ('joy/set_feedback', 'joy_teleop/joy/set_feedback'),
        ])
  
    teleop_joy = Node(
        package='teleop_twist_joy', executable='teleop_node',
        name='teleop_twist_joy_node',
        namespace=namespace,
        parameters=[config_filepath, 
                    {'publish_stamped_twist': False,
                     'use_sim_time': True,
                     }],
        remappings={('cmd_vel', launch.substitutions.LaunchConfiguration('joy_vel'))},
        )
    nodes = [joy, teleop_joy]
    return(launch.LaunchDescription(arguments + nodes))