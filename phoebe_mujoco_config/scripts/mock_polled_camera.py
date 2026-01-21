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
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from sensor_msgs.msg import Image, CameraInfo
from std_srvs.srv import Trigger

from message_filters import ApproximateTimeSynchronizer, Subscriber


class MockPolledCamera(Node):
    """
    Unlike other applications, the cameras on Phoebe are only triggered on request. This class wraps the streaming
    mujoco images to "mock" that behavior by subscribing to the streaming topics from the sim drivers, and
    republishing images only when requested.

    This is similar to a polled realsense camera from https://github.com/NASA-JSC-Robotics/realsense_polled_camera.
    """

    def __init__(self):
        super().__init__("polled_rgbd_camera_node")

        # Parameters for input topic names
        self.declare_parameter("input_color_image_topic", "/camera_/color/image_raw")
        self.declare_parameter("input_depth_image_topic", "/camera_/depth/image_raw")
        self.declare_parameter("input_camera_info_topic", "/camera_/color/camera_info")

        # Parameters for output topic names
        self.declare_parameter("output_color_image_topic", "/camera/color/image_raw")
        self.declare_parameter("output_depth_image_topic", "/camera/depth/image_raw")
        self.declare_parameter("output_camera_info_topic", "/camera/color/camera_info")

        # Synchronization parameters
        self.declare_parameter("queue_size", 10)
        self.declare_parameter("slop", 0.2)

        # Get parameters
        input_color_image_topic = self.get_parameter("input_color_image_topic").get_parameter_value().string_value
        input_depth_image_topic = self.get_parameter("input_depth_image_topic").get_parameter_value().string_value
        input_camera_info_topic = self.get_parameter("input_camera_info_topic").get_parameter_value().string_value

        output_color_image_topic = self.get_parameter("output_color_image_topic").get_parameter_value().string_value
        output_depth_image_topic = self.get_parameter("output_depth_image_topic").get_parameter_value().string_value
        output_camera_info_topic = self.get_parameter("output_camera_info_topic").get_parameter_value().string_value

        queue_size = self.get_parameter("queue_size").get_parameter_value().integer_value
        slop = self.get_parameter("slop").get_parameter_value().double_value

        # Like the realsense polled camera, these images are published on demand so they should be reliable.
        reliable_qos = QoSProfile(reliability=ReliabilityPolicy.RELIABLE, history=HistoryPolicy.KEEP_LAST, depth=10)

        # Publishers (output)
        self.color_pub = self.create_publisher(Image, output_color_image_topic, reliable_qos)
        self.depth_pub = self.create_publisher(Image, output_depth_image_topic, reliable_qos)
        self.info_pub = self.create_publisher(CameraInfo, output_camera_info_topic, reliable_qos)

        # Latest synchronized messages
        self.latest_color = None
        self.latest_depth = None
        self.latest_info = None

        # Create synchronized subscribers using message_filters
        self.color_sub = Subscriber(self, Image, input_color_image_topic)
        self.depth_sub = Subscriber(self, Image, input_depth_image_topic)
        self.info_sub = Subscriber(self, CameraInfo, input_camera_info_topic)

        # Slap them all into something that allows for some slop
        self.sync = ApproximateTimeSynchronizer(
            [self.color_sub, self.depth_sub, self.info_sub], queue_size=queue_size, slop=slop
        )
        self.sync.registerCallback(self.synchronized_callback)

        # Service
        self.srv = self.create_service(Trigger, "trigger_capture", self.handle_trigger)

        self.get_logger().info(
            f"Synchronized Polled RGB-D camera initialized:\n"
            f"  Inputs:\n"
            f"    {input_color_image_topic}\n"
            f"    {input_depth_image_topic}\n"
            f"    {input_camera_info_topic}\n"
            f"  Outputs:\n"
            f"    {output_color_image_topic}\n"
            f"    {output_depth_image_topic}\n"
            f"    {output_camera_info_topic}\n"
            f"  Sync parameters:\n"
            f"    Queue size: {queue_size}\n"
            f"    Slop: {slop}s"
        )

    def synchronized_callback(self, color_msg: Image, depth_msg: Image, info_msg: CameraInfo):
        """Callback for synchronized color, depth, and camera_info messages."""
        self.latest_color = color_msg
        self.latest_depth = depth_msg
        self.latest_info = info_msg

        self.get_logger().debug(
            f"Received synchronized messages with timestamps: "
            f"color={color_msg.header.stamp.sec}.{color_msg.header.stamp.nanosec}, "
            f"depth={depth_msg.header.stamp.sec}.{depth_msg.header.stamp.nanosec}, "
            f"info={info_msg.header.stamp.sec}.{info_msg.header.stamp.nanosec}"
        )

    def handle_trigger(self, _, response):
        """Publish the latest color, depth, and camera_info when triggered."""
        if not all([self.latest_color, self.latest_depth, self.latest_info]):
            response.success = False
            response.message = "Missing one or more inputs (color, depth, or camera info)."
            self.get_logger().warn(response.message)
            return response

        # Match timestamps for consistency (optional: you can synchronize them externally)
        stamp = self.latest_color.header.stamp

        # Just update timestamps and publish directly
        self.latest_color.header.stamp = stamp
        self.latest_depth.header.stamp = stamp
        self.latest_info.header.stamp = stamp

        # Publish all three
        self.info_pub.publish(self.latest_info)
        self.color_pub.publish(self.latest_color)
        self.depth_pub.publish(self.latest_depth)

        response.success = True
        response.message = "Published latest RGB-D frames and camera info."
        self.get_logger().info(response.message)
        return response


def main(args=None):
    rclpy.init(args=args)
    node = MockPolledCamera()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
