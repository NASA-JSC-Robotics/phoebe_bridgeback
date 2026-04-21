#!/usr/bin/env python3
#
# Copyright (c) 2025, United States Government, as represented by the
# Administrator of the National Aeronautics and Space Administration.
#
# All rights reserved.
#
# This software is licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import termios
import select
import sys
import time
import tty
import threading

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped


# Simple script for converting keyboard key input to a twist message for driving the bridgeback
class KeyboardTeleopNode(Node):

    def __init__(self):
        super().__init__("phoebe_teleop")

        # Publish twist commands at 10 hz
        self.twist = TwistStamped()
        self.last_key_time = time.time() - 0.2
        self.reset_twist()
        self.publisher_ = self.create_publisher(TwistStamped, "/cmd_vel", 1)
        self.timer = self.create_timer(0.1, self.publish_twist)
        self.running = True

        self.key_thread = threading.Thread(target=self.key_listener_loop)
        self.key_thread.daemon = True
        self.key_thread.start()

        # For configuring the terminal to go silent, but saving the state so that we
        # can reset the terminal to echo key input when the script exits
        self.fd_ = sys.stdin
        self.old_settings_ = termios.tcgetattr(self.fd_)
        self.old_settings_[3] = self.old_settings_[3] | termios.ECHO

    def shutdown(self):
        # Reset terminal to saved settings
        termios.tcsetattr(self.fd_, termios.TCSADRAIN, self.old_settings_)

        # Kill the thread, give it time to gracefully terminate
        self.running = False
        time.sleep(0.1)
        if self.key_thread.is_alive():
            self.key_thread.join()

        # Do the ROS shutdown
        super().destroy_node()

    def reset_twist(self):
        self.twist.twist.linear.x = 0.0
        self.twist.twist.angular.z = 0.0

    def key_listener_loop(self):
        # Configures the shell to read raw input
        tty.setcbreak(sys.stdin)

        while self.running:
            # Check for key presses, if nothing reloop at 50 hz
            rlist, _, _ = select.select([sys.stdin], [], [], 0.02)
            if not rlist:
                continue

            # Check for arrow key input
            key = sys.stdin.read(1)
            if key == "\x1b":
                self.last_key_time = time.time()
                key = sys.stdin.read(2)
                if key == "[A":  # Up arrow
                    self.twist.twist.linear.x = 0.1
                    self.twist.twist.angular.z = 0.0
                elif key == "[B":  # Down arrow
                    self.twist.twist.linear.x = -0.1
                    self.twist.twist.angular.z = 0.0
                elif key == "[C":  # Right arrow
                    self.twist.twist.linear.x = 0.0
                    self.twist.twist.angular.z = -0.1
                elif key == "[D":  # Left arrow
                    self.twist.twist.linear.x = 0.0
                    self.twist.twist.angular.z = 0.1
            else:
                # Stop the robot on any other key
                self.reset_twist()

    def publish_twist(self):
        if self.running:
            # If we haven't received a command in 100 ms stop the robot
            if time.time() - self.last_key_time > 0.1:
                self.reset_twist()

            self.publisher_.publish(self.twist)


def main(args=None):
    rclpy.init(args=args)
    node = KeyboardTeleopNode()
    print("Starting keyboard node (ctrl-c to quit)")

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("Shutting down keyboard joystick node...")
    finally:
        node.shutdown()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
