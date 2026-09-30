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
from rcl_interfaces.msg import ParameterDescriptor
from geometry_msgs.msg import TransformStamped
from phoebe_interfaces.srv import SetWorld
import tf2_ros


class WorldPublisher(Node):
    def __init__(self):
        super().__init__("world_publisher")
        self.setup_parameters()

        # Set TF broadcaster
        self.broadcaster = tf2_ros.TransformBroadcaster(self)

        # Service to receive the transform
        self.srv = self.create_service(SetWorld, "set_world", self.set_world_transform)

        # Timer to publish the transform repeatedly
        self.rate_hz = self.get_parameter("rate_hz").value
        self.timer = self.create_timer(1 / self.rate_hz, self.publish_world_transform)

        # Initialization of stored transform, will not publish until this is initialized.
        self.world_transform = None

    def setup_parameters(self):
        rate_param_desc = ParameterDescriptor(description="Frequency at which the frame is published.")
        self.declare_parameter("rate_hz", 5, rate_param_desc)

        world_param_desc = ParameterDescriptor(description="Name of the 'world' frame.")
        self.declare_parameter("world_frame", "world", world_param_desc)

        map_param_desc = ParameterDescriptor(description="Name of the 'map' frame.")
        self.declare_parameter("map_frame", "map", map_param_desc)

    # Receive + store transform
    def set_world_transform(self, request, response):
        self.world_transform = request.transform
        self.get_logger().info("Found world, updated transform")
        t = request.transform.translation
        r = request.transform.rotation
        self.get_logger().info(
            f"  Translation:\n"
            f"    x: {t.x:.3f}\n"
            f"    y: {t.y:.3f}\n"
            f"    z: {t.z:.3f}\n"
            f"  Rotation (quaternion):\n"
            f"    x: {r.x:.3f}\n"
            f"    y: {r.y:.3f}\n"
            f"    z: {r.z:.3f}\n"
            f"    w: {r.w:.3f}"
        )
        response.success = True
        return response

    # Publish stored transform as a TransformStamped msg via TF2
    def publish_world_transform(self):
        if self.world_transform is None:
            return

        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = self.get_parameter("world_frame").value
        t.child_frame_id = self.get_parameter("map_frame").value

        t.transform = self.world_transform  # world to map tf
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
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
