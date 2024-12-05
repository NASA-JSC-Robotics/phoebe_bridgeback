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
        default_value="false",
        description="Start robot with fake hardware mirroring command to its states.",
    )
    arg_headless_mode = DeclareLaunchArgument(
        "headless_mode",
        default_value="false",
        description="Enable headless mode for robot control",
    )
    
    # Initialize Arguments
    tf_prefix = LaunchConfiguration("tf_prefix")
    use_fake_hardware = LaunchConfiguration("use_fake_hardware")
    headless_mode = LaunchConfiguration("headless_mode")
    namespace = LaunchConfiguration("namespace")
    
    
    

    pkg_deploy = get_package_share_directory('phoebe_deploy')
    pkg_description = get_package_share_directory('phoebe_description')
    
    robot_controllers = PathJoinSubstitution(
        [
            FindPackageShare("phoebe_deploy"),
            "config",
            "control.yaml",
        ]
    )
    urdf_model_path = os.path.join(pkg_description, 'urdf/phoebe.urdf.xacro')
    
    
    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[urdf_model_path, robot_controllers],
        output="both",
#        namespace=namespace
    )

    
    
    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        name="joint_state_broadcaster_control",
        parameters=[robot_controllers],
        arguments=[ 
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager"],
    )
#    
#    joint_state_broadcaster = Node(
#        package="controller_manager",
#        executable="spawner",
#        name="joint_state_broadcaster_control",
#        parameters=[control_config],
#        arguments=[
#            "joint_state_broadcaster",
#            "--controller-manager-timeout",
#            "300",
##            "--controller-manager",
##            "/controller_manager",
#        ],
#    )
    drive_controller = Node(
            package='controller_manager',
            executable='spawner',
            name='platform_velocity_controller',
            arguments=["platform_velocity_controller", "--param-file", robot_controllers],
            output='screen'
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

    return LaunchDescription([
        arg_tf_prefix,
        arg_use_fake_hardware,
        arg_headless_mode,
        control_node,
        joint_state_broadcaster,
        drive_controller,
        start_world,
        spawn_robot,
        clock_bridge
    ])