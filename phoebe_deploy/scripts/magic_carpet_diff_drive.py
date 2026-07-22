#!/usr/bin/env python3
#
# Copyright (c) 2026, United States Government, as represented by the
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

"""
Bridges platform velocity controller commands to the magic carpet controller.
"""

import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped
from std_msgs.msg import Float64MultiArray

from phoebe_deploy.joint_state_subscriber import JointStateSubscriber

class CmdVelToMagicCarpet(Node):
    """
    Rotates body-frame cmd_vel into odom-frame velocities and
    publishes directly to the forward velocity controller.
    """

    def __init__(self):
        super().__init__("cmd_vel_to_magic_carpet")

        self.declare_parameter("tf_prefix", "")
        self.declare_parameter("cmd_vel_topic", "/platform_velocity_controller/reference")
        self.declare_parameter("joint_states_topic", "joint_states")
        self.declare_parameter("controller_name", "phoebe_magic_carpet_controller")

        tf_prefix = self.get_parameter("tf_prefix").value
        cmd_vel_topic = self.get_parameter("cmd_vel_topic").value
        joint_states_topic = self.get_parameter("joint_states_topic").value
        controller_name = self.get_parameter("controller_name").value

        self.yaw_joint_name = f"{tf_prefix}rotational_yaw_joint"

        self.joint_names = [
            f"{tf_prefix}linear_x_joint",
            f"{tf_prefix}linear_y_joint",
            f"{tf_prefix}rotational_yaw_joint",
        ]

        self.js_subscriber = JointStateSubscriber(
            node_name="cmd_vel_bridge_js_listener",
            topic=joint_states_topic,
            joint_names=self.joint_names,
        )

        self.cmd_vel_sub = self.create_subscription(
            TwistStamped, cmd_vel_topic, self.cmd_vel_callback, 10
        )

        self.cmd_pub = self.create_publisher(
            Float64MultiArray,
            f"{controller_name}/commands",
            10,
        )

        self.get_logger().info(
            f"cmd_vel -> magic carpet bridge started "
            f"(listening on {cmd_vel_topic}, "
            f"publishing to {controller_name}/commands)"
        )

    def _get_current_yaw(self):
        msg = self.js_subscriber.last_joint_state
        if msg is None:
            return None
        for i, name in enumerate(msg.name):
            if name == self.yaw_joint_name:
                return msg.position[i]
        return None

    def cmd_vel_callback(self, msg: TwistStamped):
        yaw = self._get_current_yaw()
        if yaw is None:
            return

        # Rotate body-frame velocities to the robot's frame
        cos_yaw = math.cos(yaw)
        sin_yaw = math.sin(yaw)

        vx_odom = msg.twist.linear.x * cos_yaw - msg.twist.linear.y * sin_yaw
        vy_odom = msg.twist.linear.x * sin_yaw + msg.twist.linear.y * cos_yaw

        cmd = Float64MultiArray()
        cmd.data = [vx_odom, vy_odom, msg.twist.angular.z]
        self.cmd_pub.publish(cmd)

    def destroy_node(self):
        self.js_subscriber.shutdown()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CmdVelToMagicCarpet()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
