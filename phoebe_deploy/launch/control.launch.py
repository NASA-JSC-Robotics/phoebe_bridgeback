#!/usr/bin/env python3

# Software License Agreement (BSD)
#
# @author    Roni Kreinin <rkreinin@clearpathrobotics.com>
# @copyright (c) 2023, Clearpath Robotics, Inc., All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of Clearpath Robotics nor the names of its contributors
#   may be used to endorse or promote products derived from this software
#   without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# Redistribution and use in source and binary forms, with or without
# modification, is not permitted without the express permission
# of Clearpath Robotics.
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, OpaqueFunction
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
#from clearpath_config.common.utils.dictionary import unflatten_dict
#from clearpath_config.common.utils.yaml import read_yaml
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


def generate_launch_description():
    
    
    
    controller_manager = Node(
        name='controller_manager',
        package='controller_manager',
        namespace='phoebe',
        executable='ros2_control_node',
        arguments=['--controller-manager-timeout', '60', "joint_state_broadcaster"],
        output='screen',
        additional_env={'ROS_SUPER_CLIENT': 'True'},
 #       condition=IfCondition(arg_use_sim_time),
    )
     # Add Joint State Broadcaster
    joint_state_broadcaster = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['--controller-manager-timeout', '60', 'joint_state_broadcaster'],
        output='screen',
        additional_env={'ROS_SUPER_CLIENT': 'True'},
    )
    # Add Platform Velocity Controller
    platform_velocity_controller = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['--controller-manager-timeout', '60', 'platform_velocity_controller'],
        output='screen',
        additional_env={'ROS_SUPER_CLIENT': 'True'},
    )

    ld = LaunchDescription()
    ld.add_action(controller_manager)
    ld.add_action(joint_state_broadcaster)
    ld.add_action(platform_velocity_controller)
    return ld
