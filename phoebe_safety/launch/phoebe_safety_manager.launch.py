import launch
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
 
def generate_launch_description():
    # Declare the launch argument for 'use_mock_lights'
    use_mock_lights = LaunchConfiguration('use_mock_lights', default='False')
    return LaunchDescription([
        # Declare the launch argument
        DeclareLaunchArgument(
            'use_mock_lights',
            default_value='False',
            description='Use mock lights for simulation (default: False)'
        ),
        # Launch the PhoebeSafetyManager node
        Node(
            package='phoebe_safety',
            executable='pb_safety_light_manager.py',
            name='pb_safety_light_manager',
            output='both',  # 'both' means output to both screen and log
            parameters=[{'use_mock_lights': use_mock_lights}],  # Correctly pass the configuration here
        ),
    ])
