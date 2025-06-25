from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

import os

def generate_launch_description():

    wrist_camera = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory("realsense2_camera"), "launch", "rs_launch.py")
        ),
        launch_arguments={
            "camera_name": "left_wrist_mounted_camera",
            "camera_namespace": "",
            "serial_no": "'938422070949'", # needs to be updated for actual serial number
            "rgb_camera.profile": "1280,720,30",
            "initial_reset": "true",
            "pointcloud.enable": "false",
            "align_depth.enable": "true",
        }.items(),
    )

    lift_camera = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory("realsense2_camera"), "launch", "rs_launch.py")
        ),
        launch_arguments={
            "camera_name": "right_wrist_mounted_camera",
            "camera_namespace": "",
            "serial_no": "'207122078580'", # needs to be updated for actual serial number
            "rgb_camera.profile": "1280,720,30",
            "initial_reset": "true",
            "pointcloud.enable": "false",
            "align_depth.enable": "true",
        }.items(),
    )

    return LaunchDescription([wrist_camera, lift_camera])
