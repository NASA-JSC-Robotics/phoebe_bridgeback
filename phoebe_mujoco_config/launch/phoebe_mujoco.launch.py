#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    control_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("phoebe_deploy"),
                "launch",
                "control.launch.py",
            )
        ),
        launch_arguments={
            "use_fake_hardware": "true",
            "robot_description_package": "phoebe_mujoco_config",
            "robot_description_file": "phoebe_xacro.urdf",
        }.items(),
    )

    teleop_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("phoebe_deploy"),
                "launch",
                "teleop.launch.py",
            )
        ),
        launch_arguments={
            "joystick_dev": "/dev/input/js0",
        }.items(),
    )

    return LaunchDescription([control_launch, teleop_launch])
