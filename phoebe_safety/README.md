# Phoebe Bridgeback Safety Manager Simulation Test as of 4/24/2025
## Info:
This package is for the Phoebe safety manager node: pb_safety_light_manager.py. It subscribes to the estop topic and publishes the safety state based on whether the estop is active or not. (This node will be developed further to include input from controller manager and vcan status).

There is a mock estop node that will act as the estop. Also, if you are running the "simulation" (without Arduino plugged in) - there's also a mock lights node that acts as the lights.

The following is instructions to test the current rendition of the safety manager node with the mock estop.

### Build from phoebe_bridgeback (Use add-phoebe-safety branch)
Assuming you followed the build instructions from the overall phoebe_bridgeback README.md, and have the repo built.

```console
git checkout humble-feature/add-phoebe-safety
colcon build
source install/setup.bash
```

### Run safety light manager simulation (MOCK LIGHTS):

Split the terminator into three windows.

In the first type:
```console
source install/setup.bash
ros2 run phoebe_safety pb_safety_light_manager --ros-args --param use_mock_lights:=true
```
In the second type:
```console
source install/setup.bash
ros2 run phoebe_safety mock_estop_publisher
```
In the third type:
```console
source install/setup.bash
ros2 run phoebe_safety mock_lights
```

### Run with Jodi's Arduino NeoPixel Ring (LIGHTS):

(First, plug in the arduino device (USB) to your Linux computer.)

Split the terminator into two windows.

In the first type:
```console
source install/setup.bash
ros2 run phoebe_safety pb_safety_light_manager
```
In the second type:
```console
source install/setup.bash
ros2 run phoebe_safety mock_estop_publisher
```
OR type one of these:

```console
source install/setup.bash
ros2 topic pub /emergency_stop std_msgs/Bool "data: true"
```
```console
source install/setup.bash
ros2 topic pub /emergency_stop std_msgs/Bool "data: false"
```
