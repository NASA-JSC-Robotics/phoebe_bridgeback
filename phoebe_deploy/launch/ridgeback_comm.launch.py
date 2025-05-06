from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, ExecuteProcess, OpaqueFunction, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import FindExecutable, PathJoinSubstitution, LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterFile


def launch_setup(context, *args, **kwargs):

    ns = LaunchConfiguration("ns")
    default_ns = "ridgeback"
    tf_prefix = LaunchConfiguration("tf_prefix")
    tf_prefix = tf_prefix  # dummy use to get precommit to be happy

    # Include Packages
    pkg_phoebe_deploy = FindPackageShare("phoebe_deploy")
    pkg_clearpath_ros2_socketcan_interface = FindPackageShare("clearpath_ros2_socketcan_interface")
    pkg_clearpath_ros2_socketcan_interface = FindPackageShare("clearpath_ros2_socketcan_interface")
    pkg_clearpath_diagnostics = FindPackageShare("clearpath_diagnostics")

    # config files
    config_can = PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback", "can_config.yaml"])
    setup_path = PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback"])
    analyzer_params = PathJoinSubstitution([pkg_clearpath_diagnostics, "config", "diagnostics.yaml"])

    # Declare launch files
    launch_file_receiver = PathJoinSubstitution(
        [pkg_clearpath_ros2_socketcan_interface, "launch", "receiver.launch.py"]
    )
    launch_file_sender = PathJoinSubstitution([pkg_clearpath_ros2_socketcan_interface, "launch", "sender.launch.py"])

    launch_receiver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([launch_file_receiver]),
        launch_arguments={
            "namespace": default_ns,
            "interface": "vcan0",
            "from_can_bus_topic": "vcan0/rx",
        }.items(),
    )
    launch_sender = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([launch_file_sender]),
        launch_arguments={
            "namespace": default_ns,
            "interface": "vcan0",
            "to_can_bus_topic": "vcan0/tx",
        }.items(),
    )

    # Nodes
    node_wireless_watcher = Node(
        name="wireless_watcher",
        executable="wireless_watcher",
        package="wireless_watcher",
        namespace=default_ns,
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
        namespace=default_ns,
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
        namespace=default_ns,
        output="screen",
        arguments=[
            "-s",
            setup_path,
        ],
    )

    node_micro_ros_agent = Node(
        name="micro_ros_agent",
        executable="micro_ros_agent",
        package="micro_ros_agent",
        namespace=default_ns,
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
        namespace=default_ns,
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
        namespace=default_ns,
        output="screen",
        parameters=[
            ParameterFile(config_can, allow_substs=True),
        ],
        remappings=[("platform/puma/cmd", "platform/puma/cmd_throttle")],
    )

    node_aggregator_node = Node(
        package="diagnostic_aggregator",
        executable="aggregator_node",
        namespace=default_ns,
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
        namespace=default_ns,
        output="screen",
        remappings=[
            ("/diagnostics", "diagnostics"),
            ("/diagnostics_agg", "diagnostics_agg"),
            ("/diagnostics_toplevel_state", "diagnostics_toplevel_state"),
        ],
        arguments=["-s", setup_path],
    )

    # Processes
    # note this will be incorrectly namespaced if a namespace is pushed for this file
    # this should be converted to a node so it picks up the namespace
    process_configure_mcu = ExecuteProcess(
        shell=True,
        cmd=[
            ["export ROS_DOMAIN_ID=0;"],
            [
                FindExecutable(name="ros2"),
                " service call platform/mcu/configure",
                " clearpath_platform_msgs/srv/ConfigureMcu",
                ' "{domain_id: 0,',
                f" robot_namespace: '{default_ns}'}}\"",
            ],
        ],
    )

    launches = [
        launch_receiver,
        launch_sender,
    ]
    nodes = [
        node_wireless_watcher,
        node_battery_state_estimator,
        node_battery_state_control,
        node_micro_ros_agent,
        node_lighting_node,
        node_puma_control,
        node_aggregator_node,
        node_diagnostics_updater,
    ]
    processes = [process_configure_mcu]

    ns_action = GroupAction(actions=[PushRosNamespace(ns)] + launches + nodes + processes)

    return [ns_action]


def generate_launch_description():

    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "ns",
            default_value="",
            description="Namespace for the robot.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "tf_prefix",
            default_value="",
            description="tf_prefix of the joint names, useful for \
        multi-robot setup. If changed, also joint names in the controllers' configuration \
        have to be updated.",
        )
    )

    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])
