import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument("ns", default_value="", description="Namespace for the hardware robot")
    )
    ns = LaunchConfiguration("ns")

    config_right = os.path.join(get_package_share_directory("phoebe_deploy"), "config", "pb_right.yaml")
    config_left = os.path.join(get_package_share_directory("phoebe_deploy"), "config", "pb_left.yaml")

    right_gui_node = Node(
        package="drt_ur_gui",
        executable="run_gui.py",
        name="right_drt_ur_gui",
        output="screen",
        namespace=ns,
        parameters=[config_right],
    )
    left_gui_node = Node(
        package="drt_ur_gui",
        executable="run_gui.py",
        name="left_drt_ur_gui",
        output="screen",
        namespace=ns,
        parameters=[config_left],
    )

    nodes = [right_gui_node, left_gui_node]

    return LaunchDescription(declared_arguments + nodes)
