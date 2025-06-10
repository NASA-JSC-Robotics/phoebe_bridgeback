# Phoebe Bridgeback Safety Manager Node Test

## Info:

The following is instructions to test the functionality of the safety manager node, and to help troubleshoot if need be.
We are assuming you followed the build instructions from the overall phoebe_bridgeback README.md, and have the repo built.

There is a mock estop node that can act as the estop, if you are not testing with hardware.

### Run to Test

First, plug in the arduino device (USB) to your Linux computer.
It can also plugged in after you run the node.

Split the terminator into three windows.

In the first type one of these:

```console
source install/setup.bash
ros2 launch phoebe_safety phoebe_safety_manager.launch.py
```
```console
source install/setup.bash
ros2 run phoebe_safety pb_safety_light_manager.py
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

Assuming you have the robot running on sim or hardware - and want to test controller status conditions of the safety light manager,
then in the third type the following:

Firstly, see the existing controllers list and whether they are active/inactive and what interfaces they have.

```console
ros2 control list_controllers -v
```
Next, test the node by setting all controllers inactive/active.
Type one of these:

```console
src/phoebe_bridgeback/phoebe_safety/scripts/set_all_controllers.sh inactive
```
```console
src/phoebe_bridgeback/phoebe_safety/scripts/set_all_controllers.sh active
```
Now, if you have all your controllers set to inactive - try setting a controller with command interfaces to active.
Safety status will indicate "not safe."

```console
ros2 control set_controller_state joint_trajectory_controller active
```
Lastly, have all your controller set to inactive and only set the freedrive mode controller active.
Safety status will indicate still "safe" or "caution", depending on the estop status.

```console
ros2 control set_controller_state freedrive_mode_controller inactive
```
