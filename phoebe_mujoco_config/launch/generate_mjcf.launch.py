import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
import xacro


from launch import LaunchDescription
from launch.substitutions import (
    Command,
    FindExecutable,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    phoebe_mujoco_package_name = "phoebe_mujoco_config"
    phoebe_mujoco_description_file = "phoebe_xacro.urdf"
    phoebe_mujoco_package_path = get_package_share_directory(phoebe_mujoco_package_name)

    mujoco_inputs = os.path.join(phoebe_mujoco_package_path,
                                 "description",
                                 "mujoco_inputs.xml")


    # main robot description for Phoebe
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution([FindPackageShare(phoebe_mujoco_package_name), "urdf", phoebe_mujoco_description_file]),
        ]
    )

    make_mjcf_from_robot_description = Node(
        package='mujoco_ros2_tools',
        executable='make_mjcf_from_robot_description',
        output='screen',
        arguments=[
            "-r",
            robot_description_content,
            "-m",
            mujoco_inputs,
            "-c", # convert stl to obj
        ]
    )

    return LaunchDescription([
        make_mjcf_from_robot_description,
    ])
