from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    arguments = []

    arguments.append(
        DeclareLaunchArgument(
            "tf_prefix",
            default_value='""',
            description="tf_prefix of the joint names, useful for \
        multi-robot setup. If changed, also joint names in the controllers' configuration \
        have to be updated.",
        )
    )
    arguments.append(
        DeclareLaunchArgument(
            "is_sim",
            default_value="false",
            description="Start robot with simulated hardware mirroring command to its states.",
        )
    )
    arguments.append(
        DeclareLaunchArgument(
            "headless_mode",
            default_value="false",
            description="Enable headless mode for robot control",
        )
    )

    # Initialize Arguments
    tf_prefix = LaunchConfiguration("tf_prefix")
    is_sim = LaunchConfiguration("is_sim")
    headless_mode = LaunchConfiguration("headless_mode")

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
            "headless_mode:=",
            headless_mode,
            " ",
        ]
    )
    robot_description = {"robot_description": robot_description_content}

    rviz_config_file = PathJoinSubstitution([FindPackageShare("phoebe_description"), "rviz", "view_robot.rviz"])

    joint_state_broadcaster = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description],
    )
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
    )

    nodes = [
        joint_state_broadcaster,
        robot_state_publisher,
        rviz_node,
    ]

    return LaunchDescription(arguments + nodes)
