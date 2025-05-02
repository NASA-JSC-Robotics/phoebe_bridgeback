from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    # Launch configurations
    use_mock_lights = LaunchConfiguration("use_mock_lights", default="False")
    arduino_port = LaunchConfiguration("arduino_port", default="/dev/ttyACM0")

    return LaunchDescription(
        [
            # Declare launch arguments
            DeclareLaunchArgument(
                "use_mock_lights", default_value="False", description="Use mock lights for simulation (default: False)"
            ),
            DeclareLaunchArgument(
                "arduino_port",
                default_value="/dev/ttyACM0",
                description="Serial port for Arduino (default: /dev/ttyACM0)",
            ),
            # Start the safety manager node
            Node(
                package="phoebe_safety",  # <-- Replace with your actual package name
                executable="pb_safety_light_manager.py",  # Make sure this matches your installed script name
                name="pb_safety_light_manager",
                output="both",
                parameters=[
                    {"use_mock_lights": use_mock_lights},
                    {"arduino_port": arduino_port},
                ],
            ),
        ]
    )
