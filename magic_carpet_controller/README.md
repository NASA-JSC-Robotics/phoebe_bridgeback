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
```

## Nav2 Integration

When running in magic carpet mode, SLAM and localization can optionally be disabled.
The URDF's world joints provide the ground-truth `map → odom → base_link` transform, so any SLAM will just fight it and introduce drift.

However, we note that the magic carpet can still be used in localization stacks.
Simply DO NOT publish joint states for the linear rail joints (for instance, omit them from `joint_state_broadcaster`'s joint list).
This controller's `~/odom` topic can then serve as the odometry source without interfering with the TF tree.
