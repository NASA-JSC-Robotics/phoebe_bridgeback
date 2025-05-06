# Phoebe Bridgeback Safety Manager Node Test

## Info:
This package is for the Phoebe safety manager node: pb_safety_light_manager.py. It takes info from the estop and controller manager, and publishes a safety state and light color based on the whether the estop/controllers are active. (This node will be developed further to include input from vcan status).

There is a mock estop node that will act as the estop. 

The following is instructions to test the current rendition of the safety manager node with the mock estop.

### Build from phoebe_bridgeback (Use add-phoebe-safety branch)
Assuming you followed the build instructions from the overall phoebe_bridgeback README.md, and have the repo built.

```console
git checkout humble-feature/add-phoebe-safety
colcon build
source install/setup.bash
```
### Run

(First, if you want to try with hardware - plug in the arduino device (USB) to your Linux computer.)

Split the terminator into two windows.

In the first type:
```console
source install/setup.bash
ros2 launch phoebe_safety phoebe_safety_manager.launch.py
```
In the second type:
```console
source install/setup.bash
ros2 run phoebe_safety mock_estop_publisher.py
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
