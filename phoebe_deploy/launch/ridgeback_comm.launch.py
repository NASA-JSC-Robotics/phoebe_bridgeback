from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, ExecuteProcess, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import FindExecutable, PathJoinSubstitution, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def launch_setup(context, *args, **kwargs):

    ns = LaunchConfiguration("ns")

    # Include Packages
    pkg_phoebe_deploy = FindPackageShare("phoebe_deploy")
    pkg_clearpath_ros2_socketcan_interface = FindPackageShare("clearpath_ros2_socketcan_interface")
    pkg_clearpath_ros2_socketcan_interface = FindPackageShare("clearpath_ros2_socketcan_interface")
    pkg_clearpath_diagnostics = FindPackageShare('clearpath_diagnostics')
    pkg_clearpath_sensors = FindPackageShare("clearpath_sensors")

    config_imu_filter = PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback", "imu_filter.yaml"])
    config_can = PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback", "can_config.yaml"])
    config_localization = PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback", "localization.yaml"])
    config_lidar2d = PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback", "lidar2d_0.yaml"])
    setup_path = PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback"])
    analyzer_params = PathJoinSubstitution([pkg_clearpath_diagnostics, "config", "diagnostics.yaml"])

    ns_str = ns.perform(context)
    ns_w_slash = ns_str + "/" if ns_str else ""

    # Declare launch files
    launch_file_receiver = PathJoinSubstitution(
        [pkg_clearpath_ros2_socketcan_interface, "launch", "receiver.launch.py"]
    )
    launch_file_sender = PathJoinSubstitution([pkg_clearpath_ros2_socketcan_interface, "launch", "sender.launch.py"])
    launch_file_hokuyo_ust = PathJoinSubstitution([pkg_clearpath_sensors, "launch", "hokuyo_ust.launch.py"])

    launch_receiver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([launch_file_receiver]),
        launch_arguments={
            "namespace": ns,
            "interface": "vcan0",
            "from_can_bus_topic": "vcan0/rx",
        }.items(),
    )
    launch_sender = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([launch_file_sender]),
        launch_arguments={
            "namespace": ns,
            "interface": "vcan0",
            "to_can_bus_topic": "vcan0/tx",
        }.items(),
    )

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

    # Nodes
    node_wireless_watcher = Node(
        name="wireless_watcher",
        executable="wireless_watcher",
        package="wireless_watcher",
        namespace=ns,
        output="screen",
        parameters=[
            {
                "hz": 1.0,
                "dev": "",
                "connected_topic": "platform/wifi_connected",
                "connection_topic": "platform/wifi_status",
            },
        ],
    )

    node_battery_state_estimator = Node(
        name="battery_state_estimator",
        executable="battery_state_estimator",
        package="clearpath_hardware_interfaces",
        namespace=ns,
        output="screen",
        arguments=[
            "-s",
            setup_path,
        ],
    )

    node_battery_state_control = Node(
        name="battery_state_control",
        executable="battery_state_control",
        package="clearpath_hardware_interfaces",
        namespace=ns,
        output="screen",
        arguments=[
            "-s",
            setup_path,
        ],
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

    node_micro_ros_agent = Node(
        name="micro_ros_agent",
        executable="micro_ros_agent",
        package="micro_ros_agent",
        namespace=ns,
        output="screen",
        arguments=[
            "udp4",
            "--port",
            "11411",
        ],
    )

    node_lighting_node = Node(
        name="lighting_node",
        executable="lighting_node",
        package="clearpath_hardware_interfaces",
        namespace=ns,
        output="screen",
        parameters=[
            {
                "platform": "r100",
            },
        ],
    )

    node_puma_control = Node(
        name="puma_control",
        executable="multi_puma_node",
        package="puma_motor_driver",
        namespace=ns,
        output="screen",
        parameters=[config_can],
    )

    node_aggregator_node = Node(
        package="diagnostic_aggregator",
        executable="aggregator_node",
        namespace=ns,
        output="screen",
        parameters=[analyzer_params],
        remappings=[
            ("/diagnostics", "diagnostics"),
            ("/diagnostics_agg", "diagnostics_agg"),
            ("/diagnostics_toplevel_state", "diagnostics_toplevel_state"),
        ],
    )

    node_diagnostics_updater = Node(
        package="clearpath_diagnostics",
        executable="diagnostics_updater",
        namespace=ns,
        output="screen",
        remappings=[
            ("/diagnostics", "diagnostics"),
            ("/diagnostics_agg", "diagnostics_agg"),
            ("/diagnostics_toplevel_state", "diagnostics_toplevel_state"),
        ],
        arguments=["-s", setup_path],
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

    # Processes
    process_configure_mcu = ExecuteProcess(
        shell=True,
        cmd=[
            ["export ROS_DOMAIN_ID=0;"],
            [
                FindExecutable(name="ros2"),
                " service call platform/mcu/configure",
                " clearpath_platform_msgs/srv/ConfigureMcu",
                ' "{domain_id: 0,',
                f" robot_namespace: '{ns.perform(context)}'}}\"",
            ],
        ],
    )

    launches = [
        launch_receiver,
        launch_sender,
        launch_hokuyo_ust,
    ]
    nodes = [
        node_wireless_watcher,
        node_battery_state_estimator,
        node_battery_state_control,
        node_imu_filter_madgwick,
        node_micro_ros_agent,
        node_lighting_node,
        node_puma_control,
        node_aggregator_node,
        node_diagnostics_updater,
        node_localization,
    ]
    processes = [process_configure_mcu]

    return launches + nodes + processes


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

    print("here")