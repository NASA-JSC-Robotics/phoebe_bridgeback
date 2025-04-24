from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def launch_setup(context, *args, **kwargs):

    ns = LaunchConfiguration("ns")

    # Include Packages
    pkg_phoebe_deploy = FindPackageShare("phoebe_deploy")
    pkg_clearpath_sensors = FindPackageShare("clearpath_sensors")

    config_imu_filter = PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback", "imu_filter.yaml"])
    config_localization = PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback", "localization.yaml"])
    config_lidar2d = PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback", "lidar2d_0.yaml"])

    ns_str = ns.perform(context)
    ns_w_slash = ns_str + "/" if ns_str else ""

    launch_file_hokuyo_ust = PathJoinSubstitution([pkg_clearpath_sensors, "launch", "hokuyo_ust.launch.py"])

    # Include Packages
    pkg_clearpath_sensors = FindPackageShare("clearpath_sensors")

    # Include launch files
    launch_hokuyo_ust = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([launch_file_hokuyo_ust]),
        launch_arguments={
            "parameters": config_lidar2d,
            "namespace": f"{ns_w_slash}sensors/lidar2d_0",
        }.items(),
    )

    node_imu_filter_madgwick = Node(
        name="imu_filter_madgwick",
        executable="imu_filter_madgwick_node",
        package="imu_filter_madgwick",
        namespace=ns,
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
        namespace=ns,
        output="screen",
        parameters=[config_localization],
        remappings=[
            ("odometry/filtered", "platform/odom/filtered"),
            ("/diagnostics", "diagnostics"),
            ("/tf", "tf"),
            ("/tf_static", "tf_static"),
        ],
    )

    launches = [
        launch_hokuyo_ust,
    ]
    nodes = [
        node_imu_filter_madgwick,
        node_localization,
    ]

    return launches + nodes


def generate_launch_description():

    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "ns",
            default_value="",
            description="Namespace for the robot.",
        )
    )

    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])
