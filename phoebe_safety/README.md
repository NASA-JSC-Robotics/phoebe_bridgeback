# Phoebe Bridgeback Safety Manager Node Test

## Overview:
This package is for the Phoebe safety manager node: pb_safety_light_manager.py.
The node subscribes to and takes input from the estop and controller manager.
Then it publishes a safety state and light color based on the status of the estop and controllers.
It also sends a message via serial to the Arduino controlling the lights on the robot.

The safety states are:

SAFE (Red)= Estopped!
--> Completely safe to enter robot workspace.

CAUTION (Yellow) = Not Estopped, and NO controllers are active (OR not Estopped, and only free drive controller is active).
--> Can enter robot workspace - with E-stop in hand.

NOT SAFE (Blue) = Not Estopped, and controllers with command interfaces are active.
--> Do not enter robot workspace. If you must enter, use dead-man switch.

### Run node

First, plug in the arduino device (USB) to your Linux computer.
It can also plugged in after you run the node.

In the terminator window, type one of these:

```console
source install/setup.bash
ros2 launch phoebe_safety phoebe_safety_manager.launch.py
```
```console
source install/setup.bash
ros2 run phoebe_safety pb_safety_light_manager.py
```
