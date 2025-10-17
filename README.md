# Phoebe Bridgeback

The instructions to run the whole phoebe environment can be found in the (phoebe docker workspace)[https://js-er-code.jsc.nasa.gov/imetro/robots/phoebe-bridgeback/phoebe_bridgeback_ws/-/blob/humble-feature/full-urdf/README.md]. The specific launches that are useful from this repository are the following

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
```
