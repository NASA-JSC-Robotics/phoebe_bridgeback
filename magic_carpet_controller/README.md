# Magic Carpet Controller

Provides a `ros2_controller` implementation of a "Magic Carpet" for a wheeled base robot.

In some simulation environments wheeled mobile robots can be tricket to match to hardware.
Slipping, acceleration, and other sim-specific dynamics can cause all kinds of issues.
The magic carpet sidesteps this by replacing the wheel joints with prismatic and revolute "world joints" (linear X, linear Y, rotational yaw) that move the base directly in the odom frame.

So the robot will "glide" as if on a magic carpet.

## Interfaces

This controller subscribes to body-frame `TwistStamped` commands, rotates them into the odom frame using the current yaw joint state, and writes the resulting velocities directly to the magic carpet joint command interfaces.

**Command interfaces (velocity):** `linear_x_joint`, `linear_y_joint`, `rotational_yaw_joint`

**State interfaces (position):** `rotational_yaw_joint`

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
    reference_topic: /platform_velocity_controller/reference_unstamped
```

## Nav2 Integration

When running in magic carpet mode, SLAM and localization should be disabled.
The URDF's world joints will provide the full `map → odom → base_link`, so any SLAM will just fight the ground-truth transform and introduce drift.
