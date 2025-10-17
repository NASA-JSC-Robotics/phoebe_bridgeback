import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration

from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():

    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "rviz",
            default_value="true",
            description="start rviz?",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "ns",
            default_value="",
            description="Namespace for the robot.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "calibration_mode",
            default_value="false",
            description="Whether or not we are running the calibration routine",
            choices=["true", "false"],
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="false",
            description="If the robot is running in simulation, use the published clock",
        )
    )

    rviz = LaunchConfiguration("rviz")
    ns = LaunchConfiguration("ns")
    calibration_mode = LaunchConfiguration("calibration_mode")
    use_sim_time = LaunchConfiguration("use_sim_time")

    description_package = "phoebe_description"
    description_file = "phoebe.urdf.xacro"
    description_full_path = os.path.join(get_package_share_directory(description_package), "urdf", description_file)
    description_mappings = {"calibration_mode": calibration_mode}

    moveit_config = (
        MoveItConfigsBuilder("phoebe", package_name="phoebe_moveit_config")
        .robot_description(file_path=description_full_path, mappings=description_mappings)
        .robot_description_semantic(file_path="config/phoebe.srdf", mappings=description_mappings)
        .robot_description_kinematics(file_path="config/kinematics.yaml")
        .joint_limits(file_path="config/joint_limits.yaml")
        .trajectory_execution(file_path="config/moveit_controllers.yaml")
        .to_moveit_configs()
    )

    nodes_to_start = []

    nodes_to_start.append(
        Node(
            package="moveit_ros_move_group",
            executable="move_group",
            output="both",
            namespace=ns,
            parameters=[
                {"use_sim_time": use_sim_time},
                moveit_config.to_dict(),
            ],
        )
    )

    rviz_config_file = os.path.join(get_package_share_directory("phoebe_moveit_config"), "config", "moveit.rviz")
    rviz_qss_file = os.path.join(get_package_share_directory("phoebe_moveit_config"), "config", "dark.qss")

    nodes_to_start.append(
        Node(
            package="rviz2",
            executable="rviz2",
            name="rviz2_moveit",
            output="log",
            namespace=ns,
            arguments=["-d", rviz_config_file, "--stylesheet", rviz_qss_file],
            parameters=[
                {"use_sim_time": use_sim_time},
                moveit_config.robot_description,
                moveit_config.robot_description_semantic,
                moveit_config.robot_description_kinematics,
                moveit_config.planning_pipelines,
                moveit_config.joint_limits,
                moveit_config.planning_scene_monitor,
            ],
            condition=IfCondition(rviz),
        )
    )

    return LaunchDescription(declared_arguments + nodes_to_start)
