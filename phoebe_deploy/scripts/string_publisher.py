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


import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSDurabilityPolicy
from std_msgs.msg import String


class StringPublisher(Node):
    """Publishes a string parameter on a topic with transient local durability.

    Intended for publishing a robot_description URDF to a separate topic so that
    nodes like ros2_control_node can subscribe to a different description than
    the one published by robot_state_publisher.
    """

    def __init__(self):
        super().__init__("string_publisher")

        self.declare_parameter("content", "")
        self.declare_parameter("topic", "robot_description")

        content = self.get_parameter("content").value
        topic = self.get_parameter("topic").value

        if not content:
            self.get_logger().error("No content provided, nothing to publish")
            return

        # Transient local so late subscribers still have access
        qos = QoSProfile(depth=1, durability=QoSDurabilityPolicy.TRANSIENT_LOCAL)
        pub = self.create_publisher(String, topic, qos)
        pub.publish(String(data=content))

        self.get_logger().info(f"Published {len(content)} bytes on '{topic}' (transient local)")


def main(args=None):
    rclpy.init(args=args)
    node = StringPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
