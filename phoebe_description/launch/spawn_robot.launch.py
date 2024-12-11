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
    
    arg_use_sim_time = DeclareLaunchArgument(
        'use_fake_hardware',
        default_value="true",
        description='use_fake_hardware'
    )
    arg_tf_prefix = DeclareLaunchArgument(
        'tf_prefix',
        default_value='/',
        description='tf_prefix'
    )

    use_fake_hardware = LaunchConfiguration('use_fake_hardware')
    tf_prefix = LaunchConfiguration('tf_prefix')

    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution([FindPackageShare("phoebe_description"), "urdf", "phoebe.urdf.xacro"]),
#            " ",
#            "tf_prefix:=",
#            tf_prefix,
            " ",
            "is_sim:=",
            use_fake_hardware,
#            " ",
#            "headless_mode:=",
#            headless_mode,
        ]
    )
    print(robot_description_content)
    robot_description = {"robot_description": robot_description_content}

    
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description],
    )
    
    # Spawn the robot in Gazebo
    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-entity", "phoebe",
            "-name", "phoebe",
            "-topic", "/robot_description",
            "-x", "0",
            "-y", "0",
            "-z", "1.4",
            "-controller_manager", "controller_manager"
        ],
        output="screen",
    )

    # Launch!
    return LaunchDescription(
        [
            arg_use_sim_time,
            arg_tf_prefix,
            robot_state_publisher,
            spawn_entity,
        ]
    )


