import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, SetEnvironmentVariable, 
                            IncludeLaunchDescription, SetLaunchConfiguration)
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration, TextSubstitution
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import FindExecutable
from launch.actions import ExecuteProcess



def generate_launch_description():
    
    
    namespace = LaunchConfiguration("ns")
    
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    pkg_deploy = get_package_share_directory('phoebe_deploy')
    pkg_description = get_package_share_directory('phoebe_description')
    gz_launch_path = PathJoinSubstitution([pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py'])
    gz_model_path = PathJoinSubstitution([pkg_description, 'urdf'])
    
    
    world = str(os.path.join(pkg_deploy, 'worlds', 'empty_world.sdf'))

    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value='empty_world',
            description='World to load into Gazebo'
        ),
        SetLaunchConfiguration(name='world_file', 
                               value=[LaunchConfiguration('world'), 
                                      TextSubstitution(text='.sdf')]),
        SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH', gz_model_path),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(gz_launch_path),
            launch_arguments={
                'gz_args': ['-r -v 4 ' + world], # -r to unpause the sim (required to load controls) -v verbose
                'on_exit_shutdown': 'True'
            }.items(),
        ),
        #bridge communication between ros and gazebo
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='sim_comm_bridge',
            namespace=namespace,
            parameters=[{
                'config_file': os.path.join(pkg_deploy, 'config', 'bridge.yaml'),
                'qos_overrides./tf_static.publisher.durability': 'transient_local',
            }],
            output='screen'
        ),
    ])