#!/usr/bin/env python3

# Copyright 2024 PickNik Inc.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#    * Neither the name of the PickNik Inc. nor the names of its
#      contributors may be used to endorse or promote products derived from
#      this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import rclpy
from rclpy.node import Node

from nav_msgs.msg import Odometry
from sensor_msgs.msg import JointState

from rclpy.qos import (
    QoSProfile,
    QoSReliabilityPolicy,
    QoSDurabilityPolicy,
    QoSHistoryPolicy,
)
from math import atan2


class OdometryJointStateRepublisher(Node):
    """
    Handles converting odometry and world apriltag offsets to joint states.

    Publishes joint states for the virtual links that connect the base link of phoebe to odom,
    and therefore both map and the world.
    """

    def __init__(self, odom_topic, joint_states_topic, publish_rate_hz=50):
        super().__init__("odometry_joint_state_republisher")

        self.latest_odom = None
        self.joint_state_msg = JointState()
        self.joint_state_msg.name = [
            "linear_x_joint",
            "linear_y_joint",
            "rotational_yaw_joint",
        ]

        # Use these to update the pose of the robot in world coordinates, including offsets
        self.correction_x = 0.0
        self.correction_y = 0.0
        self.correction_yaw = 0.0
        self.localized = False

        # QoS profiles
        qos_profile_sub = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
        )

        qos_profile_pub = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.VOLATILE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
        )

        # Subscriber and publisher
        self.odom_sub = self.create_subscription(
            Odometry, odom_topic, self.odom_callback, qos_profile_sub
        )
        self.joint_states_pub = self.create_publisher(
            JointState, joint_states_topic, qos_profile_pub
        )

        # Timer for publishing
        timer_period = 1.0 / publish_rate_hz
        self.timer = self.create_timer(timer_period, self.publish_joint_states)

        self.get_logger().info("Odometry to JointState republisher started")

    def odom_callback(self, odom_msg):
        self.latest_odom = odom_msg

    def publish_joint_states(self):
        if self.latest_odom is None:
            return

        odom_x = self.latest_odom.pose.pose.position.x
        odom_y = self.latest_odom.pose.pose.position.y
        odom_yaw = self.quat_to_yaw(self.latest_odom.pose.pose.orientation)
        stamp = self.latest_odom.header.stamp

        self.joint_state_msg.header.stamp = stamp
        self.joint_state_msg.position = [odom_x, odom_y, odom_yaw]

        # Constant
        self.joint_state_msg.velocity = [0.0, 0.0, 0.0]
        self.joint_state_msg.effort = [0.0, 0.0, 0.0]

        self.joint_states_pub.publish(self.joint_state_msg)

    def quat_to_yaw(self, q):
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        return atan2(siny_cosp, cosy_cosp)


def main(args=None):
    rclpy.init(args=args)
    node = OdometryJointStateRepublisher("/ridgeback/odometry/filtered", "/joint_states")

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
