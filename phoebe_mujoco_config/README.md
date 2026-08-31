# Phoebe Mujoco Config

Mujoco configuration for launching Phoebe in a simulated Mujoco environment.

## Wheels vs Magic Carpet

By default, running Phoebe in MuJoCo will use the converted "wheels" to mimic hardware.
These wheels are actually a set of rollers that are added to the converted MJCF by [this script](./scripts/wheel_code_gen.py).
These can be difficult for localization purposes, as MuJoCo's wheels tend to slip.

To alleviate the difficulties of modeling wheels, we provide an optional "magic carpet" to bypass these problems.
When running in magic carpet mode, the wheels are replaced by two linear rails and a yaw joint to mimic mecanum drive motion.

The [magic carpet controller](./../magic_carpet_controller/README.md) subscribes to body-frame `TwistStamped` commands, just like a mecanum drive.
The controller rotates the twists into the odom frame using the current yaw, and writes the velocities directly to the "world joints" (linear X, linear Y, rotational yaw).
This way, the robot glides without any actual wheel dynamics.

To launch magic carpet mode:

```bash
# Launches the MuJoCo sim with a magic carpet
ros2 launch phoebe_mujoco_config phoebe_mujoco.launch.py magic_carpet:=true

# Be sure to let nav2 know, as odomety and slam will be adjusted
ros2 launch phoebe_nav2_config phoebe_nav.launch.py use_sim_time:=true magic_carpet:=true
```

In both magic carpet mode and wheel mode, the controller manager receives the full URDF (with world joints) on a separate topic than the robot state publisher (RSP) via `string_publisher.py`.
In wheel mode, the description passed to the RSP and controller manager match.

In magic carpet mode, the localization pipeline is simplified because the world joints provide ground-truth position:

- **Wheel controllers** — the `platform_velocity_controller` and `odom_publisher` are not spawned.
The magic carpet controller handles both command input and odometry output.
- **EKF** — `ridgeback_sensors` (which contains `robot_localization`'s `ekf_node`) is disabled.
The EKF cannot pass through perfect odometry losslessly and introduces drift, so it is bypassed entirely.
The magic carpet publishes odom directly on `ridgeback/odometry/filtered`.
- **SLAM TF** — `slam_toolbox`'s `map -> odom` transform publishing is disabled.
Instead, a static identity `map -> odom` transform is published.
- **Robot State Publisher** — RSP receives a URDF without world joints (different from the URDF with world joints passed to the controller manager) so it doesn't publish `odom -> base_link` through the URDF joint chain.
The magic carpet controller owns that transform directly.
