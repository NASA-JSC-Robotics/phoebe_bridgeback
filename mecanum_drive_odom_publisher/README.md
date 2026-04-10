# Mecanum Drive Odometry Publisher

## Description

The mecanum drive odom publisher is a controller designed to work with in parallel to the clearpath mecanum_drive_controller.
It basically just uses the odom portion of that controller, but the idea is that this controller can stay up permanently and not affect the safety of the robot.

## Usage

* You should set up the controller config similarly to how you set up the mecanum_drive_controller, because it uses all of the same odom information. An example is below for the ridgeback.

```yaml
  controller_manager:
    odom_publisher:
        type: mecanum_drive_odom_publisher/MecanumDriveOdomPublisher

  odom_publisher:
    ros__parameters:
      use_sim_time: False
      interface_name: 'velocity'

      state_joint_names: [$(var tf_prefix)front_left_wheel_joint, $(var tf_prefix)rear_left_wheel_joint, $(var tf_prefix)rear_right_wheel_joint, $(var tf_prefix)front_right_wheel_joint]

      kinematics.base_frame_offset:
        x: 0.0
        y: 0.0
        theta: 0.0
      kinematics.wheels_radius: 0.0759
      kinematics.sum_of_robot_center_projection_on_X_Y_axis: 0.59

      wheel_separation_multiplier: 1.0
      wheel_radius_multiplier: 1.0

      pose_covariance_diagonal: [0.001, 0.001, 1000000.0, 1000000.0, 1000000.0, 0.03]
      twist_covariance_diagonal: [0.001, 0.001, 0.001, 1000000.0, 1000000.0, 0.03]

      base_frame_id: $(var tf_prefix)base_link
      odom_frame_id: $(var tf_prefix)odom
      enable_odom_tf: False

```

## Notes

* The testing is not yet setup, so it is just commented out in the CMakeLists.txt.
