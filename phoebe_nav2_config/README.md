# Phoebe Nav2 Config

Phoebe comes with a basic nav2 integration that works on hardware and in the dynamic simulation.
The topics are all intended to match across systems.

## Diagram

Wiring nav2 together and figuring out where it is disconnected can be difficult.
The diagram below is a rough map of the nodes, topics, and controllers involved.
When things aren't working it should give users a rough idea of where connections are made.

```mermaid
graph TD
    subgraph Hardware / Mujoco Outputs
        WHEELS[Mecanum Drive]
        IMU_HW[IMU Sensor]
        LIDAR_HW[Clearpath Hokuyo Lidar\nOr Mujoco Lidar]
    end

    subgraph ros2_control
        PVC[platform_velocity_controller]
        ODOM_PUB[odom_publisher]
        IMU_BC[imu_broadcaster]
    end

    WHEELS --> PVC
    WHEELS --> ODOM_PUB
    IMU_HW --> IMU_BC
    LIDAR_HW -->|sensor_msgs/msg/LaserScan| LIDAR_TOPIC([ridgeback/sensors/lidar2d_0/scan])

    PVC -->|nav_msgs/msg/Odometry| ODOM_TOPIC([platform_velocity_controller/odometry])
    ODOM_PUB -->|nav_msgs/msg/Odometry| ODOM2_TOPIC([odom_publisher/odom])
    IMU_BC -->|sensor_msgs/msg/Imu| IMU_TOPIC([ridgeback/sensors/imu_0/data_raw])

    subgraph Nav2 Localization
        IMU_FILTER[imu_filter_madgwick]
        EKF[ekf_node]
        SLAM_TB[slam_toolbox]
    end

    IMU_TOPIC --> IMU_FILTER
    IMU_FILTER --> EKF
    ODOM_TOPIC --> EKF
    ODOM2_TOPIC --> EKF

    EKF -->|"TF: odom -> base_link"| TF_TREE([TF Tree])
    EKF -->|nav_msgs/msg/Odometry| FILTERED_ODOM([odometry/filtered])

    LIDAR_TOPIC --> SLAM_TB
    SLAM_TB -->|"TF: map → odom"| TF_TREE
    SLAM_TB -->|nav_msgs/msg/OccupancyGrid| MAP_TOPIC([map])

    subgraph Nav2 Planning
        NAV2[bt_navigator \n planner_server \n controller_server \n global_costmap \n local_costmap \n etc]
        NOTE[This is a bit of a block box\nconfigured in the nav2 yaml]
    end

    MAP_TOPIC -->|nav_msgs/msg/OccupancyGrid| NAV2
    LIDAR_TOPIC -->|sensor_msgs/msg/LaserScan| NAV2
    TF_TREE --> NAV2
    FILTERED_ODOM -->|nav_msgs/msg/Odometry| NAV2

    VEL_SMOOTH[velocity_smoother]
    COLL_MON[collision_monitor]

    NAV2 -->|geometry_msgs/msg/Twist| CMD_NAV([cmd_vel_nav])
    CMD_NAV -->|geometry_msgs/msg/Twist| VEL_SMOOTH
    VEL_SMOOTH -->|geometry_msgs/msg/Twist| CMD_SMOOTH([cmd_vel_smoothed])
    CMD_SMOOTH -->|geometry_msgs/msg/Twist| COLL_MON
    COLL_MON -->|geometry_msgs/msg/Twist| CMD_VEL([cmd_vel])

    subgraph Command Muxing
        TWIST_MUX[twist_mux]
        JOY([joy_teleop/cmd_vel])
        RC([rc_teleop/cmd_vel])
        TWIST_SRV([twist_marker_server/cmd_vel])
    end

    CMD_VEL -->|geometry_msgs/msg/Twist| TWIST_MUX
    JOY -->|geometry_msgs/msg/Twist| TWIST_MUX
    RC -->|geometry_msgs/msg/Twist| TWIST_MUX
    TWIST_SRV -->|geometry_msgs/msg/Twist| TWIST_MUX

    TWIST_MUX -->|geometry_msgs/msg/Twist| REF_TOPIC([platform_velocity_controller/reference_unstamped])
    REF_TOPIC --> PVC_INPUT

    subgraph Hardware / Mujoco Inputs
        PVC_INPUT[Mecanum Drive]
    end
```
