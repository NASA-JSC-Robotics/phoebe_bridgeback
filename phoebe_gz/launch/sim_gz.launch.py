#!/usr/bin/python3
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, OpaqueFunction, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import PushRosNamespace
from launch.conditions import IfCondition

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
        default_value="true",
        description="Start robot with simulated hardware mirroring command to its states.",
    )
)
arguments.append(DeclareLaunchArgument("ns", default_value=""))


def launch_setup(context):

    # Initialize Arguments
    tf_prefix = LaunchConfiguration("tf_prefix")
    is_sim = LaunchConfiguration("is_sim")
    namespace = LaunchConfiguration("ns").perform(context)

    if not namespace:
        use_namespace = "False"
    else:
        use_namespace = "True"

    if use_namespace == "True":
        print("*************************", namespace, "**********************************")

    pkg_deploy = get_package_share_directory("phoebe_deploy")
    pkg_description = get_package_share_directory("phoebe_description")

    # Start gazebo with the selected World
    world_group = GroupAction(
        [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(os.path.join(pkg_deploy, "launch", "start_world.launch.py"))
            )
        ]
    )

    # add the robot to the world

    robot_group = GroupAction(
        [
            PushRosNamespace(condition=IfCondition([use_namespace]), namespace=namespace),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(os.path.join(pkg_description, "launch", "spawn_robot.launch.py")),
                launch_arguments={
                    "is_sim": is_sim,
                    "tf_prefix": tf_prefix,
                    #                                'namespace' : namespace
                }.items(),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(os.path.join(pkg_deploy, "launch", "control.launch.py")),
                launch_arguments={
                    "is_sim": is_sim,
                    "tf_prefix": tf_prefix,
                    "namespace": namespace,
                }.items(),
            ),
        ]
    )
    nodes = (world_group, robot_group)

    return nodes


def generate_launch_description():
    n = OpaqueFunction(function=launch_setup)
    ld = LaunchDescription(arguments)
    ld.add_action(n)
    return ld
