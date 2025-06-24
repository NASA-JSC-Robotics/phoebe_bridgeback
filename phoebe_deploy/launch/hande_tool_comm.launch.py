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
        name="right_ur_tool_communication_hande",
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
        name="left_ur_tool_communication_hande",
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

    r_urscript_interface = Node(
        package="ur_robot_driver",
        executable="urscript_interface",
        name="right_urscript_interface",
        parameters=[{"robot_ip": "192.168.131.41"}],
        output="screen",
    )

    r_dashboard_client_node = Node(
        package="ur_robot_driver",
        executable="dashboard_client",
        name="right_dashboard_client",
        output="screen",
        emulate_tty=True,
        parameters=[{"robot_ip": "192.168.131.41"}],
    )

    l_urscript_interface = Node(
        package="ur_robot_driver",
        executable="urscript_interface",
        name="left_urscript_interface",
        parameters=[{"robot_ip": "192.168.131.40"}],
        output="screen",
    )

    l_dashboard_client_node = Node(
        package="ur_robot_driver",
        executable="dashboard_client",
        name="left_dashboard_client",
        output="screen",
        emulate_tty=True,
        parameters=[{"robot_ip": "192.168.131.40"}],
    )

    nodes = [
        hande_right_comm_node,
        hande_left_comm_node,
        r_urscript_interface,
        r_dashboard_client_node,
        l_urscript_interface,
        l_dashboard_client_node,
    ]

    return LaunchDescription(declared_arguments + nodes)
