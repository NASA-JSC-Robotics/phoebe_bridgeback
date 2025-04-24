# Phoebe Bridgeback Safety Manager Simulation Test as of 4/23/2025
## Info: 
This package is for the Phoebe safety manager node. It subscribes to the estop topic and publishes the safety state based on whether the estop is active or not. (This node will be developed further to include input from controller manager and vcan status). 

There is an additional mock estop node that will act as the estop. The following is instructions to test the current rendition of the safety manager node with the mock estop. 

### Build from phoebe_bridgeback (Use add-phoebe-safety branch)
Assuming you followed the build instructions from the overall phoebe_bridgeback README.md, and have the repo built.

```console
git checkout humble-feature/add-phoebe-safety
colcon build
source install/setup.bash
```

### Run

Split the terminator into two windows.  

In the first type:
```console
source install/setup.bash
ros2 run phoebe_safety mock_estop_publisher
```
In the second type:
```console
source install/setup.bash
ros2 run phoebe_safety pb_safety_light_manager
```
