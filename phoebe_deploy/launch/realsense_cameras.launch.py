from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

import os


def generate_launch_description():

    left_camera = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory("realsense2_camera"), "launch", "rs_launch.py")
        ),
        launch_arguments={
            "camera_name": "left_wrist_mounted_camera",
            "camera_namespace": "",
            "serial_no": "'207522078043'",
            "rgb_camera.color_profile": "1280,720,6",
            # "depth_module.depth_profile": "320,180,6",
            # "depth_module.infra_profile": "320,180,6",
            "initial_reset": "true",
            "pointcloud.enable": "false",
            "align_depth.enable": "false",
            "enable_depth": "false",
        }.items(),
    )

    right_camera = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory("realsense2_camera"), "launch", "rs_launch.py")
        ),
        launch_arguments={
            "camera_name": "right_wrist_mounted_camera",
            "camera_namespace": "",
            "serial_no": "'207522073775'",  # needs to be updated for actual serial number
            "rgb_camera.color_profile": "1280,720,6",
            # "depth_module.depth_profile": "320,180,6",
            # "depth_module.infra_profile": "320,180,6",
            "initial_reset": "true",
            "pointcloud.enable": "false",
            "align_depth.enable": "false",
            "enable_depth": "false",
        }.items(),
    )

    return LaunchDescription([left_camera, right_camera])
    # return LaunchDescription([right_camera])
