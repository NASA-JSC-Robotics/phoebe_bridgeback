import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration, Command, PathJoinSubstitution, FindExecutable
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import launch_ros.descriptions
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():

    is_sim = LaunchConfiguration('use_fake_hardware')
    tf_prefix = LaunchConfiguration('tf_prefix')
    namespace = LaunchConfiguration('ns')
    
    arguments = []
    
    arguments.append(DeclareLaunchArgument(
        'use_fake_hardware',
        default_value="true",
        description='use_fake_hardware'
    ))
    arguments.append(DeclareLaunchArgument(
        'tf_prefix',
        default_value="",
        description="tf_prefix of the joint names, useful for \
        multi-robot setup. If changed, also joint names in the controllers' configuration \
        have to be updated.",
    ))
    arguments.append(DeclareLaunchArgument(
        'ns',
        default_value="/",
    ))


    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution([FindPackageShare("phoebe_description"), "urdf", "phoebe.urdf.xacro"]),
            " ",
            "tf_prefix:=",
            tf_prefix,
            " ",
            "is_sim:=",
            is_sim,
            " ",
            "namespace:=",
            namespace
#            " ",
#            "headless_mode:=",
#            headless_mode,
        ]
    )
    robot_description = {"robot_description": robot_description_content}

    
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        namespace=namespace,
        output="screen",
        parameters=[robot_description],
    )
    
    # Spawn the robot in Gazebo
    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        namespace=namespace,
        arguments=[
            "-entity", "phoebe",
            "-name", "phoebe",
            "-topic", "robot_description",
            "-x", "0",
            "-y", "0",
            "-z", "1.4",
            "-controller_manager", "controller_manager"
        ],
        output="screen",
    )

    nodes = [robot_state_publisher, spawn_entity]
 
    return LaunchDescription(arguments + nodes)