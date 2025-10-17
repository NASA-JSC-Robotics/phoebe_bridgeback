from launch import LaunchDescription
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.parameter_descriptions import ParameterFile


def generate_launch_description():
    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "config_filename",
            default_value="left_camera_config.yaml",
            description="which camera filename to run",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "namespace",
            default_value="left_wrist_mounted_camera",
            description="namespace - make sure this matches the camera name",
        )
    )

    config_filename = LaunchConfiguration("config_filename")
    namespace = LaunchConfiguration("namespace")

    config_filepath = PathJoinSubstitution(
        [
            FindPackageShare("phoebe_calibration"),
            "config",
            config_filename,
        ]
    )

    hand_eye_cal = Node(
        name="hand_eye_cal",
        namespace=namespace,
        package="hand_eye_cal_ros2",
        executable="hand_eye_cal_node",
        remappings=[
            ("color_image", "color/image_raw"),
            ("camera_info", "color/camera_info"),
        ],
        output="screen",
        parameters=[ParameterFile(config_filepath)],
    )

    return LaunchDescription(declared_arguments + [hand_eye_cal])
