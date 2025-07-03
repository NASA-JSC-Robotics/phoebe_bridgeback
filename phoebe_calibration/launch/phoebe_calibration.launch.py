from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    # Launch configurations
    robot_side = LaunchConfiguration("robot_side")

    return LaunchDescription(
        [
            # Declare launch arguments
            DeclareLaunchArgument(
                "robot_side",
                default_value="right",
                description="Which robot arm is doing the calibration",
                choices=["left", "right"],
            ),
            # Start the safety manager node
            Node(
                package="phoebe_calibration",  # <-- Replace with your actual package name
                executable="phoebe_calibration.py",  # Make sure this matches your installed script name
                name="phoebe_calibration",
                output="both",
                parameters=[
                    {"robot_side": robot_side},
                ],
            ),
        ]
    )
