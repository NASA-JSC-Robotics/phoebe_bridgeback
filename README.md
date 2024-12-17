# Phoebe Bridgeback Simulation
## Install
### Build from Source
#### Dependencies

- [Robot Operating System (ROS)](http://wiki.ros.org) (middleware for robotics)
- [robot_state_publisher](http://wiki.ros.org/robot_state_publisher) (allows you to publish the state of a robot to tf2)
- [urdf](http://wiki.ros.org/urdf)(contains a number of XML specifications for robot models, sensors, scenes, etc.)
- [xacro](http://wiki.ros.org/xacro)(XML macro language)
- [ros_gz_bridge](https://docs.ros.org/en/humble/p/ros_gz_bridge/)(Bridge communication between ROS and Gazebo Transport)
- [ros2_control] (https://control.ros.org/humble/index.html)(a framework for (real-time) control of robots using ROS2)
- [ign_ros2_control](https://docs.ros.org/en/humble/p/ign_ros2_control/)(allows to control simulated robots using ros2_control framework--note that this changes to gz_ros_control for gazebo harmonic)
- [controller_manager](https://control.ros.org/humble/doc/ros2_control/controller_manager/doc/userdoc.html) (main component of the ROS2 control framework)
- [clearpath_desktop](https://github.com/clearpathrobotics/clearpath_desktop) We really only need clearpath_platform for the Puma controller when using real hardware, and clearpath_platform_description for a few materials.  Clearpath has this all bundled up together, so we have to have the dang thing.
- [ros_gz_sim](https://docs.ros.org/en/humble/p/ros_gz_sim/) Tools for using Gazebo Sim simulation with ROS.
- [rviz2]

#### Build
```console
mkdir -p sim_ws/src
cd !$
git checkout git@js-er-code.jsc.nasa.gov:imetro/robots/phoebe-bridgeback/phoebe_bridgeback.git
cd ../
git apt update
rosdep install --from-paths ./src --ignore-src -y
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash
```

## Run
```console
ros2 launch phoebe_deploy simulate.launch.py
```

If you have a usb joystick, in another window run:

```console
ros2 launch phoebe_deploy joy_sim.launch
```

Currently set up with Teleop enable on button 7 (larger right side trigger)
Linear axes are on the right side thumb stick, x vertical (positive up) and y horizontal (positive left)
Rotation is on the left side thumb stick horizontal axis, left for positive yaw.
### Running in Docker

Make sure to [install Docker](https://docs.docker.com/get-docker/) first. 

First, spin up a simple container:
```console
docker pull osrf/ros:humble-desktop
xhost +local:root

docker run -it --network host --privileged -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix -v /dev:/dev -v path-to-your-workspace/src:/root/phoebe_ws/src osrf/ros:humble-desktop

```
Tip: Create a bash script with those commands
	
This will start a docker with ros2/humble installed. Type
```Console
cd
sudo apt update
cd apt install terminator -y (because you will need two terminals)
cd phoebe_ws
rosdep install --from-paths ./src --ignore-src -y
source /opt/ros/humble/setup.bash
colcon build

termimator
```
Split the terminator into two windows.  In the first type:
```console
source install/setup.bash
ros2 launch phoebe_deploy simulate.launch.py
```
In the second type:
```console
source install/setup.bash
ros2 launch phoebe_deploy joy_sim.launch.py
```
Drive the simulation using the joystick.  You can use the teleop panel in Gazebo to drive the robot--/cmd_vel and use the buttons, sliders or keyboard to drive. This doesn't support motion in the y direction.  If you want to namespace the teleop panel, you can change the name of the command on the panel, but you also need to change the gz_topic_name in the bridge.yaml file.

## Config files

Config files in phoebe_description

* **bridge.yaml** mapping between ros topics and gazebo topics used by gz_ros_bridge

Config files in phoebe_deploy

* **control.yaml** parameters for the ros controllers (no tf_prefix)
* **phoebe_control.yaml** parameters for the ros controllers (tf_prefix = phoebe_)
* **joy_config.yaml** parameters mapping joystick action


## Launch files

In phoebe_description:

* **view_robot.launch.py:** Brings up the robot in rviz, with a joint_state_publisher and joint_state_publisher_gui.  The gui is needed to manage the wheel links

     Arguments:

     - **`tf_prefix`** Prefix for all of the frame ids. Default: `""`.
     - **`is_sim`** Sets the is_sim parameter in the xacro, so that it uses the simulated hardware. Default: `False`.
     - **`headless_mode`** Currently unused

* **spawn_robot.launch.py:** spawns the simulated robot and the gz to ros bridge for the simulation.  Add topics to config/bridge.yaml
when new simulated topics are added, such as cameras, imus etc.

     Arguments:
     - **`tf_prefix`** Prefix for all of the frame ids. Default: `""`.
     - **`is_sim`** Sets the is_sim parameter in the xacro, so that it uses the simulated hardware. Default: `False`.

In phoebe_deploy:

* **bridge.launch.py:** Brings up the gazebo/ros bridge

* **control.launch.py:** brings up the ROS controls

* **start_world.launch.py:** brings up the gazebo simulator with the selected world
    Arguments:
     - **`world`** Name of the world to load. Default: `empty_world.sdf`.

* **simulate.launch.py:** Launches start.world.launch.py, control.launch.py, and spawn_robot.launch.py with the correct namespace

     Arguments:

     - **`tf_prefix`** Prefix for all of the frame ids. Default: `""`.
     - **`is_sim`** Sets the is_sim parameter in the xacro, so that it uses the simulated hardware. Default: `True`.
     - **`headless_mode`** Currently unused

* **joy_sim.launch.py:** starts the joystick interface
    Arguments:
     
    - **`joy_vel`** output topic for commanded velocity. Default:`cmd_vel_unstamped`
    - **`joy_dev`** which joystick device to use. Default:`0`

