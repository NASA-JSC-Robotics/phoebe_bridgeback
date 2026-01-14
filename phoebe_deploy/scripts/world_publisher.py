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


import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Transform, TransformStamped
from phoebe_interfaces.srv import SetWorld
import tf2_ros


class WorldPublisher(Node):
    def __init__(self):
        super().__init__("world_publisher")

        # Set TF broadcaster
        self.broadcaster = tf2_ros.TransformBroadcaster(self)

        # Service to receive the transform
        self.srv = self.create_service(SetWorld, "set_world", self.set_world_transform)

        # Timer to publish the transform repeatedly
        self.rate_hz = 5  # TODO: Adjust as needed.
        self.timer = self.create_timer(1 / self.rate_hz, self.publish_world_transform)

        # Initialization of stored transform, defaults to an empty transform.
        self.world_transform = Transform()

    # Receive + store transform
    def set_world_transform(self, request, response):
        self.world_transform = request.transform
        self.get_logger().info("Found world.")
        response.success = True
        return response

    # Publish stored transform as a TransformStamped msg via TF2
    def publish_world_transform(self):
        if self.world_transform is None:
            return

        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = "map"
        t.child_frame_id = "world"

        t.transform = self.world_transform  # map to world tf
        self.broadcaster.sendTransform(t)


def main(args=None):
    rclpy.init(args=args)
    node = WorldPublisher()
    print("Starting the world to map republisher...")

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.shutdown()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
