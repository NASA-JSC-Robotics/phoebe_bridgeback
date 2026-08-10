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

import select
import sys
import termios
import threading
import time
import tty

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node

LINEAR_SPEED = 0.1
ANGULAR_SPEED = 0.1

PUBLISH_PERIOD = 0.1
KEY_POLL_PERIOD = 0.02
# This is a bit annoying but bumping this up to avoid the OS key dedupe limit
KEY_TIMEOUT = 0.6

ARROW_UP = "[A"
ARROW_DOWN = "[B"
ARROW_RIGHT = "[C"
ARROW_LEFT = "[D"


class KeyboardTeleopNode(Node):
    def __init__(self):
        super().__init__("phoebe_teleop")

        self.twist = Twist()
        self.reset_twist()
        self.last_key_time = time.time() - KEY_TIMEOUT * 2
        self.running = True

        self.publisher_ = self.create_publisher(Twist, "/cmd_vel", 1)
        self.timer = self.create_timer(PUBLISH_PERIOD, self.publish_twist)

        self.key_thread = threading.Thread(target=self.key_listener_loop, daemon=True)
        self.key_thread.start()

        # Save terminal settings so we can restore echo on exit
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

        super().destroy_node()

    def reset_twist(self):
        self.twist.linear.x = 0.0
        self.twist.angular.z = 0.0

    def set_twist(self, linear, angular):
        self.twist.linear.x = linear
        self.twist.angular.z = angular

    def key_listener_loop(self):
        # Configures the shell to read raw input
        tty.setcbreak(sys.stdin)

        while self.running:
            # Poll for a key; if none, loop again at requested period
            rlist, _, _ = select.select([sys.stdin], [], [], KEY_POLL_PERIOD)
            if not rlist:
                continue

            key = sys.stdin.read(1)
            if key == "\x1b":
                # Arrow keys arrive as ESC + 2 bytes
                self.last_key_time = time.time()
                seq = sys.stdin.read(2)
                if seq == ARROW_UP:
                    self.set_twist(LINEAR_SPEED, 0.0)
                elif seq == ARROW_DOWN:
                    self.set_twist(-LINEAR_SPEED, 0.0)
                elif seq == ARROW_RIGHT:
                    self.set_twist(0.0, -ANGULAR_SPEED)
                elif seq == ARROW_LEFT:
                    self.set_twist(0.0, ANGULAR_SPEED)
            else:
                # Stop the robot on any other key
                self.reset_twist()

    def publish_twist(self):
        if not self.running:
            return

        # Stop the robot if we haven't seen a recent arrow-key press
        if time.time() - self.last_key_time > KEY_TIMEOUT:
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
