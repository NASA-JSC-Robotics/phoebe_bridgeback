
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, OpaqueFunction
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory

REMAPPINGS = [
    ('joint_states', 'platform/joint_states'),
    ('dynamic_joint_states', 'platform/dynamic_joint_states'),
    ('platform_velocity_controller/odom', 'platform/odom'),
    ('platform_velocity_controller/cmd_vel_unstamped', 'platform/cmd_vel_unstamped'),
    ('platform_velocity_controller/reference', 'platform/cmd_vel_unstamped'),
    ('/diagnostics', 'diagnostics'),
    ('/tf', 'tf'),
    ('/tf_static', 'tf_static'),
    ('~/robot_description', 'robot_description'),
]

controller_manager_name = '/controller_manager'

def generate_launch_description():
    
    deploy_pkg = get_package_share_directory('phoebe_deploy')
    
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{
            'config_file': os.path.join(deploy_pkg, 'config', 'bridge.yaml'),
            'qos_overrides./tf_static.publisher.durability': 'transient_local',
        }],
        output='screen'
    )

 # Configs
    ld = LaunchDescription()
    ld.add_action(bridge)

    return(ld)