#!/bin/bash
ros2 topic pub /cmd_vel geometry_msgs/msg/TwistStamped "header:
  stamp: now
  frame_id: ''
twist:
  linear:
    x: 0.1
    y: 0.0
    z: 0.0
  angular:
    x: 0.0
    y: 0.0
    z: 0.0
"
