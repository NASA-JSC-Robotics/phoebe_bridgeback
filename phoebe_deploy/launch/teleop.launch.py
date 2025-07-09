from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node


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
            "use_sim_time", choices=["true", "false"], default_value="false", description="Use simulation time"
        )
    )

    # Launch Configurations
    ns = LaunchConfiguration("ns")
    use_sim_time = LaunchConfiguration("use_sim_time")

    # Include Packages
    pkg_phoebe_deploy = FindPackageShare("phoebe_deploy")
    pkg_phoebe_safety = FindPackageShare("phoebe_safety")

    # config files
    config_teleop_joy = PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback", "teleop_joy.yaml"])
    config_twist_mux = PathJoinSubstitution([pkg_phoebe_deploy, "config", "ridgeback", "twist_mux.yaml"])
    config_teleop_interactive_markers = PathJoinSubstitution(
        [pkg_phoebe_deploy, "config", "ridgeback", "teleop_interactive_markers.yaml"]
    )

    config_joystick_safing = PathJoinSubstitution([pkg_phoebe_safety, "config", "pb_joystick_actions.yaml"])

    node_joy = Node(
        package="joy_linux",
        executable="joy_linux_node",
        namespace=ns,
        output="screen",
        name="joy_node",
        parameters=[config_teleop_joy, {"use_sim_time": use_sim_time}],
        remappings=[
            ("/diagnostics", "diagnostics"),
            ("/tf", "tf"),
            ("/tf_static", "tf_static"),
            ("joy", "joy_teleop/joy"),
            ("joy/set_feedback", "joy_teleop/joy/set_feedback"),
        ],
    )

    node_teleop_twist_joy = Node(
        package="teleop_twist_joy",
        executable="teleop_node",
        namespace=ns,
        output="screen",
        name="teleop_twist_joy_node",
        parameters=[config_teleop_joy, {"use_sim_time": use_sim_time}],
        remappings=[
            ("joy", "joy_teleop/joy"),
            ("cmd_vel", "joy_teleop/cmd_vel"),
        ],
    )

    node_interactive_marker_twist_server = Node(
        package="interactive_marker_twist_server",
        executable="marker_server",
        namespace=ns,
        name="twist_server_node",
        remappings=[
            ("cmd_vel", "twist_marker_server/cmd_vel"),
            ("twist_server/feedback", "twist_marker_server/feedback"),
            ("twist_server/update", "twist_marker_server/update"),
        ],
        parameters=[config_teleop_interactive_markers, {"use_sim_time": use_sim_time}],
        output="screen",
    )

    node_twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        namespace=ns,
        output="screen",
        remappings={
            ("cmd_vel_out", "platform_velocity_controller/cmd_vel_unstamped"),
            ("/diagnostics", "diagnostics"),
            ("/tf", "tf"),
            ("/tf_static", "tf_static"),
        },
        parameters=[config_twist_mux, {"use_sim_time": use_sim_time}],
    )

    node_joystick_safing = Node(
        package="phoebe_safety",
        executable="pb_joystick_safing.py",
        namespace=ns,
        output="screen",
        name="pb_joystick_safing",
        parameters=[
            {"actions_file": config_joystick_safing},
        ],
    )

    nodes = [
        node_joy,
        node_teleop_twist_joy,
        node_interactive_marker_twist_server,
        node_twist_mux,
        node_joystick_safing,
    ]

    return LaunchDescription(declared_arguments + nodes)
