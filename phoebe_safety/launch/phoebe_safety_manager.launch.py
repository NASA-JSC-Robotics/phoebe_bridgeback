from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    # Launch configurations
    arduino_port = LaunchConfiguration("arduino_port", default="/dev/safety_light")

    return LaunchDescription(
        [
            # Declare launch arguments
            DeclareLaunchArgument(
                "arduino_port",
                default_value="/dev/safety_light",
                description="Serial port for Arduino (default: /dev/safety_light)",
            ),
            # Start the safety manager node
            Node(
                package="phoebe_safety",  # <-- Replace with your actual package name
                executable="pb_safety_light_manager.py",  # Make sure this matches your installed script name
                name="pb_safety_light_manager",
                output="both",
                parameters=[
                    {"arduino_port": arduino_port},
                ],
            ),
        ]
    )
