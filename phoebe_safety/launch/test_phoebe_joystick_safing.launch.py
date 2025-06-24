from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

# Test launch file for joystick safing. This launch file launches a joystick safing
# node with a test config file set up to support generation of successful and
# failed service requests and functions.


def generate_launch_description():
    # Launch configurations
    actions_file = LaunchConfiguration("actions_file")
    axis_tolerance = LaunchConfiguration("axis_tolerance")

    return LaunchDescription(
        [
            # Declare launch arguments
            DeclareLaunchArgument(
                "actions_file",
                default_value=PathJoinSubstitution(
                    [FindPackageShare("phoebe_safety"), "config", "test_pb_joystick_actions.yaml"]
                ),
                description="Path to joystick actions file",
            ),
            DeclareLaunchArgument(
                "axis_tolerance", default_value="0.01", description="How much axis movement constitutes 'movement'"
            ),
            # Start the safety manager node
            Node(
                package="phoebe_safety",
                executable="pb_joystick_safing.py",
                name="pb_joystick_safing",
                output="both",
                parameters=[
                    {"actions_file": actions_file},
                    {"axis_tolerance": axis_tolerance},
                ],
            ),
        ]
    )
