from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "ns",
            default_value="",
            description="Namespace for the robot.",
        )
    )

    ns = LaunchConfiguration("ns")
    default_ns = "ridgeback"

    # Include Packages
    pkg_phoebe_deploy = FindPackageShare("phoebe_deploy")
    pkg_clearpath_sensors = FindPackageShare("clearpath_sensors")

    config_imu_filter = PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback", "imu_filter.yaml"])
    config_localization = PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback", "localization.yaml"])
    config_lidar2d = PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback", "lidar2d_0.yaml"])

    launch_file_hokuyo_ust = PathJoinSubstitution([pkg_clearpath_sensors, "launch", "hokuyo_ust.launch.py"])

    # Include Packages
    pkg_clearpath_sensors = FindPackageShare("clearpath_sensors")

    # Include launch files
    launch_hokuyo_ust = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([launch_file_hokuyo_ust]),
        launch_arguments={
            "parameters": config_lidar2d,
            "namespace": f"{default_ns}/sensors/lidar2d_0",
        }.items(),
    )

    node_imu_filter_madgwick = Node(
        name="imu_filter_madgwick",
        executable="imu_filter_madgwick_node",
        package="imu_filter_madgwick",
        namespace=default_ns,
        output="screen",
        remappings=[
            ("imu/data_raw", "sensors/imu_0/data_raw"),
            ("imu/mag", "sensors/imu_0/magnetic_field"),
            ("imu/data", "sensors/imu_0/data"),
            ("/tf", "tf"),
        ],
        parameters=[
            config_imu_filter,
        ],
    )

    node_localization = Node(
        package="robot_localization",
        executable="ekf_node",
        name="ekf_node",
        namespace=default_ns,
        output="screen",
        parameters=[config_localization],
        remappings=[
            ("~/odometry/filtered", "platform/odom/filtered"),
            ("~/diagnostics", "diagnostics"),
            ("~/tf", "tf"),
            ("~/tf_static", "tf_static"),
        ],
    )

    launches = [
        launch_hokuyo_ust,
    ]
    nodes = [
        node_imu_filter_madgwick,
        node_localization,
    ]

    ns_action = GroupAction(actions=[PushRosNamespace(ns)] + launches + nodes)

    return LaunchDescription(declared_arguments + [ns_action])
