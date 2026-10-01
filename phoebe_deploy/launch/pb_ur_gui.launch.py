import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch.conditions import IfCondition, UnlessCondition


def generate_launch_description():

    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument("namespace", default_value="", description="Namespace for the hardware robot")
    )
    declared_arguments.append(
        DeclareLaunchArgument("use_one_window", default_value="true", description="Use the same window or nah?")
    )

    namespace = LaunchConfiguration("namespace")
    use_one_window = LaunchConfiguration("use_one_window")

    config_right = os.path.join(get_package_share_directory("phoebe_deploy"), "config", "pb_right.yaml")
    config_left = os.path.join(get_package_share_directory("phoebe_deploy"), "config", "pb_left.yaml")

    gui_node = Node(
        package="drt_ur_gui",
        executable="run_gui.py",
        output="screen",
        namespace=namespace,
        parameters=[config_left, config_right],
        condition=IfCondition(use_one_window),
    )

    right_gui_node = Node(
        package="drt_ur_gui",
        executable="run_gui.py",
        name="right_drt_ur_gui",
        output="screen",
        namespace=namespace,
        parameters=[config_right],
        condition=UnlessCondition(use_one_window),
    )
    left_gui_node = Node(
        package="drt_ur_gui",
        executable="run_gui.py",
        name="left_drt_ur_gui",
        output="screen",
        namespace=namespace,
        parameters=[config_left],
        condition=UnlessCondition(use_one_window),
    )

    nodes = [right_gui_node, left_gui_node, gui_node]

    return LaunchDescription(declared_arguments + nodes)
