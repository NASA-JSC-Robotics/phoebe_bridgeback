import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    LaunchConfiguration,
)
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "ns",
            default_value="",
            description="Namespace for the robot.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "remote_control",
            default_value="true",
            description="Informs launch of UR communication setting, set to false if local to suppress UR GUIs",
            choices=["true", "false"],
        )
    )

    ns = LaunchConfiguration("ns")
    remote_control = LaunchConfiguration("remote_control")

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

    gui = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory("drt_ur_gui"), "launch", "pb.launch.py")
        ),
        condition=IfCondition(remote_control),
    )

    nodes = [
        hande_right_comm_node,
        hande_left_comm_node,
        r_dashboard_client_node,
        l_dashboard_client_node,
    ]

    launches = [gui]

    return LaunchDescription(declared_arguments + nodes + launches)
