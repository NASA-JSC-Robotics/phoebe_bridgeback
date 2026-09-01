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
        LIDAR_HW[Clearpath Hokuyo Lidar<br>Or Mujoco Lidar]
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

    subgraph Nav2 Stack
        NAV["Nav2 Stack! <br> (see below for more info)"]
    end

    LIDAR_TOPIC -->|sensor_msgs/msg/LaserScan| NAV
    TF_TREE --> NAV
    FILTERED_ODOM -->|nav_msgs/msg/Odometry| NAV

    NAV -->|geometry_msgs/msg/TwistStamped| CMD_VEL([cmd_vel])

    subgraph Command Muxing
        TWIST_MUX[twist_mux]
        JOY([joy_teleop/cmd_vel])
        RC([rc_teleop/cmd_vel])
        TWIST_SRV([twist_marker_server/cmd_vel])
    end

    CMD_VEL -->|geometry_msgs/msg/TwistStamped| TWIST_MUX
    JOY -->|geometry_msgs/msg/TwistStamped| TWIST_MUX
    RC -->|geometry_msgs/msg/TwistStamped| TWIST_MUX
    TWIST_SRV -->|geometry_msgs/msg/TwistStamped| TWIST_MUX

    TWIST_MUX -->|geometry_msgs/msg/TwistStamped| REF_TOPIC([platform_velocity_controller/reference])
    REF_TOPIC --> PVC_INPUT

    subgraph Hardware / Mujoco Inputs
        PVC_INPUT[Mecanum Drive]
    end
```

A closer look at the Nav2 stack:

```mermaid
graph TD

NOTE[Not launched from Nav2 stack: <br> docking_server <br> route_server <br> smoother_server]

LIFECYCLE["lifecycle_manager <br> (manages all Nav2 nodes)"]

NAVIGATE{{navigate_to_pose}}
BT[bt_navigator]
NAVIGATOR[bt_navigator_navigate_to_pose]
RECOVERY{{"backup, spin, wait <br> (recovery behaviors)"}}
PLAN{{compute_path_to_pose}}
CONTROL{{follow_path}}
BEHAVIOR[behavior_server]
PLANNER[planner_server]
CONTROLLER[controller_server]
GLOBAL[global_costmap]
LOCAL[local_costmap]
VEL_SMOOTH[velocity_smoother]
CMD_NAV([cmd_vel_nav])
COLL_MON[collision_monitor]
CMD_SMOOTH([cmd_vel_smoothed])

WAYPOINT["application <br> (or Nav2 waypoint_follower)"]

BT -->|navigator| NAVIGATOR
NAVIGATOR -->|"nav2_msgs/action/[Backup/Spin/Wait]"| RECOVERY
RECOVERY --> BEHAVIOR
NAVIGATOR -->|nav2_msgs/action/ComputePathToPose| PLAN
PLAN --> PLANNER
PLANNER -->|manages| GLOBAL
NAVIGATOR -->|nav2_msgs/action/FollowPath| CONTROL
CONTROL --> CONTROLLER
CONTROLLER -->|manages| LOCAL
WAYPOINT -->|nav2_msgs/action/NavigateToPose| NAVIGATE
NAVIGATE --> BT

CONTROLLER -->|geometry_msgs/msg/TwistStamped| CMD_NAV
CMD_NAV -->|geometry_msgs/msg/TwistStamped| VEL_SMOOTH
VEL_SMOOTH -->|geometry_msgs/msg/TwistStamped| CMD_SMOOTH
CMD_SMOOTH -->|geometry_msgs/msg/TwistStamped| COLL_MON
COLL_MON -->|geometry_msgs/msg/TwistStamped| CMD_VEL([cmd_vel])
```

## Debugging

Since Nav2 involves so many nodes working together, it can be difficult to debug or diagnose what the problem may be when navigation behaviors do not perform as expected.
A few things we have found helpful:

- **Planned Paths**: Check the planned path from the `planner_server` seems reasonable.
In RViz, inspect the path (`nav_msgs/msg/Path`) on topic `plan`.
- **Controller Commands**: Check the velocity command topics from the Nav2 stack:
  - `cmd_vel_nav`: output from `controller_server`
  - `cmd_vel_smoothed`: output from `velocity_smother`
  - `cmd_vel`: output from `collision_monitor`, which is sent to the platform's `twist_mux` to command the robot
- **Robot Footprint**: Check the robot's footprint against the obstacles.
In RViz, inspect the footprint polygon (`geometry_msgs/msg/PolygonStamped`) on topic `local_costmap/published_footprint` and local and global costmaps (`nav_msgs/msg/OccupancyGrid`) on topics `local_costmap/costmap` and `global_costmap/costmap` respectively.
- **Collisions**: The `collision_monitor` node is configured to clip velocity commands to prevent collisions based on the robot's configured polygons.
If one of the monitor's polygons triggers an event to clip the commands, the responsible polygon will be published as a `nav2_msgs/msg/CollisionMonitorState` to topic `collision_monitor_state`.
