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
    
    bridge_config = PathJoinSubstitution(
        [
            FindPackageShare("phoebe_deploy"),
            "config",
            "bridge.yaml",
        ]
    )
    
    # Initialize Arguments
    tf_prefix = LaunchConfiguration("tf_prefix")
    use_fake_hardware = LaunchConfiguration("use_fake_hardware")
    headless_mode = LaunchConfiguration("headless_mode")
    namespace = LaunchConfiguration("namespace")
    
    
    

    pkg_deploy = get_package_share_directory('phoebe_deploy')
    pkg_description = get_package_share_directory('phoebe_description')
    
    
    joint_state_publisher_gui = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
    )
    


    # Clock bridge
    clock_bridge = Node(package='ros_gz_bridge',
                        executable='parameter_bridge',
                        name='clock_bridge',
                        output='screen',
                        arguments=[
                          '/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock'
                        ])

    
    # Sart gazebo with the selected World
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
    
#    node_cmd_vel_bridge = Node(
#        name='cmd_vel_bridge',
#        executable='parameter_bridge',
#        package='ros_gz_bridge',
#        output='screen',
#        arguments=[bridge_config],
#        arguments=
#            ['cmd_vel@geometry_msgs/msg/Twist[ignition.msgs.Twist', 
#             '/model/phoebe/robot/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist',
#            ],
#        remappings=
#            [
#                ('phoebe/cmd_vel', '/cmd_vel' ) ,
#                ('/model/phoebe/robot/cmd_vel', '/platform/cmd_vel_unstamped'),
#            ],
#        parameters=
#            [
#                {'use_sim_time': True,},
#            ],
#    )
    
    node_odom_base_tf_bridge = Node(
        name='odom_base_tf_bridge',
        executable='parameter_bridge',
        package='ros_gz_bridge',
        output='screen',
        arguments=
            ['/model/phoebe/robot/tf@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V',],
        remappings=
            [
                ('/model/phoebe/robot/tf','/tf'),
            ],
        parameters=
            [
                {'use_sim_time': True,},
            ],
    )

 # Configs



    return LaunchDescription([
        arg_tf_prefix,
        arg_use_fake_hardware,
        arg_headless_mode,
#        node_cmd_vel_bridge,
#        node_odom_base_tf_bridge,
        start_world,
        spawn_robot,
        joint_state_publisher_gui,
#        clock_bridge,
    ])