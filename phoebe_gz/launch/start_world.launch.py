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
    
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    pkg_deploy = get_package_share_directory('phoebe_deploy')
    pkg_description = get_package_share_directory('phoebe_description')
    gz_launch_path = PathJoinSubstitution([pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py'])
    gz_model_path = PathJoinSubstitution([pkg_description, 'urdf'])
    
    
    
    world = str(os.path.join(pkg_deploy, 'worlds', 'empty_world.sdf'))
    
    arguments = []
    arguments.append(DeclareLaunchArgument(
            'world',
            default_value='empty_world',
            description='World to load into Gazebo'
        ))
    
    actions = []
    actions.append(SetLaunchConfiguration(name='world_file', 
                               value=[LaunchConfiguration('world'), 
                                      TextSubstitution(text='.sdf')]))
    actions.append(SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH', gz_model_path))
    actions.append(IncludeLaunchDescription(
            PythonLaunchDescriptionSource(gz_launch_path),
            launch_arguments={
                'gz_args': ['-r -v 4 ' + world], # -r to unpause the sim (required to load controls) -v verbose
                'on_exit_shutdown': 'True'
            }.items(),
        ))
    
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='clock_bridge',
        arguments=['/camera@rosgraph_msgs/msg/Clock[gz.msgs.Clock',],
        output='screen'
    )
    nodes = []
    nodes.append(clock_bridge)
    
    return(LaunchDescription(arguments + actions + nodes))