import os
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "model_env",
            default_value="false",
            description="Use full iMETRO environment + robot description and publish mockup joint states.",
        )
    )
    model_env = LaunchConfiguration("model_env")

    clr_mujoco_package_name = "clr_mujoco_config"
    clr_mujoco_description_file = "clr_xacro.urdf"
    clr_mujoco_package_path = get_package_share_directory(clr_mujoco_package_name)

    urdf = os.path.join(clr_mujoco_package_path,
                        "urdf",
                        clr_mujoco_description_file)

    clr_mujoco_config = os.path.join(clr_mujoco_package_path,
                                         "description",
                                         "scene.xml")

    controllers_file = os.path.join(clr_mujoco_package_path,
                                    "config",
                                    "controllers.yaml")

    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution([FindPackageShare("clr_mujoco_config"), "urdf", "clr_xacro.urdf"]),
            " ",
            "model_env:=",
            model_env
        ]
    )
    robot_description = {"robot_description": robot_description_content}

    # All time should come from the mujoco system
    use_sim_time = {'use_sim_time': True}

    # All time will come from the Mujoco control node
    use_sim_time = {'use_sim_time': True}

    mujoco_ros2_control = Node(
        package='controller_manager',
        executable='ros2_control_node',
        output='both',
        parameters=[
            robot_description,
            controllers_file,
            use_sim_time,
        ]
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[
            use_sim_time,
            robot_description,
        ]
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "-c",
            "/controller_manager",
            "--controller-manager-timeout",
            "30",
        ],
    )

    joint_trajectory_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_trajectory_controller",
            "-c",
            "/controller_manager",
            "--controller-manager-timeout",
            "30",
            "--inactive",
        ],
    )

    clr_joint_trajectory_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "clr_joint_trajectory_controller",
            "-c",
            "/controller_manager",
            "--controller-manager-timeout",
            "30",
        ],
    )

    force_torque_sensor_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "force_torque_sensor_broadcaster",
            "-c",
            "/controller_manager",
            "--controller-manager-timeout",
            "30",
        ],
    )

    robotiq_gripper_hande_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "robotiq_gripper_hande_controller",
            "-c",
            "/controller_manager",
            "--controller-manager-timeout",
            "30",
        ],
    )

    return LaunchDescription(
        declared_arguments +
        [
            mujoco_ros2_control,
            robot_state_publisher,
            joint_state_broadcaster_spawner,
            clr_joint_trajectory_controller_spawner,
            joint_trajectory_controller_spawner,
            force_torque_sensor_broadcaster_spawner,
            robotiq_gripper_hande_controller_spawner,
        ]
    )
