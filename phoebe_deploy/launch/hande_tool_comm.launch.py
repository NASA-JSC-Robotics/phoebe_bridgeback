from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import (
    LaunchConfiguration,
)
from launch_ros.actions import Node


def generate_launch_description():

    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "ns",
            default_value="",
            description="Namespace for the robot.",
        )
    )

    ns = LaunchConfiguration("ns")

    hande_right_comm_node = Node(
        name="ur_tool_communication_hande_right",
        package="ur_robot_driver",
        executable="tool_communication.py",
        namespace=ns,
        output="both",
        parameters=[
            {
                "robot_ip": "192.168.131.41",
                "device_name": "/tmp/hande_right",
            }
        ],
    )

    hande_left_comm_node = Node(
        name="ur_tool_communication_hande_left",
        package="ur_robot_driver",
        executable="tool_communication.py",
        namespace=ns,
        output="both",
        parameters=[
            {
                "robot_ip": "192.168.131.40",
                "device_name": "/tmp/hande_left",
            }
        ],
    )

    nodes = [
        hande_right_comm_node,
        hande_left_comm_node,
    ]

    return LaunchDescription(declared_arguments + nodes)
