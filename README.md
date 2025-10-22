# Phoebe Bridgeback

Descriptions, deployments, tooling, and configuration files for the Phoebe Bridgeback dual arm mobile manipulation robot platform,
part of the [iMETRO Facility](https://ntrs.nasa.gov/citations/20240013956) at NASA's Johnson Space Center.
This project is intended for use in one of ER4's managed workspaces (such as the in the [phoebe_bridgeback_ws](https://github.com/NASA-JSC-Robotics/phoebe_bridgeback_ws)).

The robot includes:

* 2x UR10e serial manipulators with Robotiq Hand-E Gripper and wrist mounted RealSense RGB-D cameras
* 2x Ewellix Lifts
* A Clearpath Ridgeback mobile base

![alt text](./phoebe_bridgeback.png "Phoebe Bridgeback MockUp")

## Usage

The instructions to run the whole phoebe environment can be found in the (Docker workspace)[].
The specific launches that are useful from this repository are the following:

```bash
# run the standard control script with a kinematics simulation
ros2 launch phoebe_deploy control.launch.py platform:=mock_hardware

# run the standard control script on hardware
ros2 launch phoebe_deploy control.launch.py platform:=hardware

# for any of these launches, you can add a namespace or tf prefix
# like the following (only shown for mock_hardware). Note that these
# have not been coordinated with the moveit config yet.
ros2 launch phoebe_deploy control.launch.py platform:=mock_hardware ns:=r100_0564
ros2 launch phoebe_deploy control.launch.py platform:=mock_hardware tf_prefix:=r100_0564_
ros2 launch phoebe_deploy control.launch.py platform:=mock_hardware ns:=r100_0564 tf_prefix:=r100_0564_

# run the standard moveit config (same for all platforms)
ros2 launch phoebe_moveit_config phoebe_moveit.launch.py

# Hardware cameras launch file
ros2 launch phoebe_deploy phoebe_rspc_camera.launch.py
```
