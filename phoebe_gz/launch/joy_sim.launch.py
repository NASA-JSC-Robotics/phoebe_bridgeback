#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os

from ament_index_python.packages import get_package_share_directory

import launch
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch_ros.actions import Node, PushRosNamespace
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition


arguments = []
arguments.append(DeclareLaunchArgument('joy_vel', default_value='cmd_vel_unstamped'))
arguments.append(DeclareLaunchArgument('joy_dev', default_value='0'))
arguments.append(DeclareLaunchArgument('publish_stamped_twist', default_value='false'))
arguments.append(DeclareLaunchArgument('ns', default_value=""))

arguments.append(DeclareLaunchArgument('config_filepath', default_value=[
        launch.substitutions.TextSubstitution(text=os.path.join(
            get_package_share_directory('phoebe_deploy'), 'config', '')),
        'joy_config', launch.substitutions.TextSubstitution(text='.yaml')]))
    

def launch_setup(context):
    
    joy_dev = LaunchConfiguration('joy_dev')
    publish_stamped_twist = LaunchConfiguration('publish_stamped_twist')
    config_filepath = LaunchConfiguration('config_filepath')
    namespace = LaunchConfiguration("ns")

    
    namespace = LaunchConfiguration("ns").perform(context)
    
    if not namespace:
        use_namespace = "False"
    else:
        use_namespace = "True"

    if use_namespace == "True":
        print("*************************", namespace, "**********************************") 
    
    
    push_ns = PushRosNamespace(
       condition=IfCondition([use_namespace]),
        namespace=namespace)
    
    joy = Node(
        package='joy', 
        executable='joy_node', 
        name='joy_node',
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
        parameters=[config_filepath, 
                    {'publish_stamped_twist': False,
                     'use_sim_time': True,
                     }],
        remappings={('cmd_vel', launch.substitutions.LaunchConfiguration('joy_vel'))},
        )
    
    nodes = (
              push_ns,
              joy, 
              teleop_joy
    )
    return nodes
    

def generate_launch_description():
    n = OpaqueFunction(function=launch_setup)
    ld = LaunchDescription(arguments)
    ld.add_action(n)
    return ld