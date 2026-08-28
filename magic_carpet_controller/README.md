# Magic Carpet Controller

Provides a `ros2_controller` implementation of a "Magic Carpet" for a wheeled base robot.

In some simulation environments wheeled mobile robots can be tricky to match to hardware.
Slipping, acceleration, and other sim-specific dynamics can cause all kinds of issues.
The magic carpet sidesteps this by replacing the wheel joints with prismatic and revolute "world joints" (linear X, linear Y, rotational yaw) that move the base directly in the odom frame.

So the robot will "glide" as if on a magic carpet.

## Interfaces

This controller subscribes to body-frame `TwistStamped` commands, rotates them into the odom frame using the current yaw joint state, and writes the resulting velocities directly to the magic carpet joint command interfaces.

**Command interfaces (velocity):** `linear_x_joint`, `linear_y_joint`, `rotational_yaw_joint`

**State interfaces (position):** `linear_x_joint`, `linear_y_joint`, `rotational_yaw_joint`

## Odometry Publisher

The controller publishes `nav_msgs/Odometry` on `~/odom` at a configurable rate.
Pose is read directly from the joint position state interfaces (odom-frame), and twist is reported in the body frame.
Set `odom_publish_rate` to `0` to disable.

## TF Broadcaster

If `publish_tf` is set, the controller broadcasts the `odom -> base_link` transform directly from the world joint positions at the same rate as the odometry publisher.
This bypasses the need for an EKF to produce the `odom -> base_link` transform.

Set `publish_tf` to `false` if something else (e.g. `robot_localization`) should own that transform.

## Example Configuration

```yaml
controller_manager:
  ros__parameters:
    magic_carpet_controller:
      type: phoebe_controllers/MagicCarpetController

magic_carpet_controller:
  ros__parameters:
    linear_x_joint: linear_x_joint
    linear_y_joint: linear_y_joint
    yaw_joint: rotational_yaw_joint
    reference_topic: /platform_velocity_controller/reference
    odom_publish_rate: 50.0
    odom_frame_id: odom
    base_frame_id: base_link
    publish_tf: true
```

## Nav2 Integration

When running in magic carpet mode, we should disable localization.
The magic carpet controller publishes both the odom topic and the `odom -> base_link` TF directly from ground truth.
Running an EKF on top of perfect odometry only introduces drift!

SLAM can remain enabled.
It will add small scan-matching noise to the `map -> odom` correction, but with perfect underlying odometry this stays bounded and exercises the same pipeline as hardware.

Ensure the world joints (linear x, linear y, yaw) are **not** published by `joint_state_broadcaster`, so `robot_state_publisher` doesn't produce a competing `odom -> base_link` chain from the URDF.
