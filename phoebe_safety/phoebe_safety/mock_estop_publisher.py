#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from std_srvs.srv import Trigger
import random
import time


class MockEstopPublisher(Node):
    def __init__(self):
        super().__init__("mock_estop_publisher")

        # Publishing to the /emergency_stop topic
        self.publisher = self.create_publisher(Bool, "/ridgeback/platform/emergency_stop", 10)

        # Create a mock controller stop service that succeeds
        self.create_service(Trigger, "~/request_freedrive_mode_succeed", self.trigger_succeed)

        # Create a mock controller stop service that fails
        self.create_service(Trigger, "~/request_freedrive_mode_fail", self.trigger_fail)

        # Create a mock controller stop service that succeeds
        self.create_service(Trigger, "~/request_restart_mode_succeed", self.trigger_succeed)

        # Create a mock controller stop service that fails
        self.create_service(Trigger, "~/request_restart_mode_fail", self.trigger_fail)

        # Publishing a new random bool every declared rate (Hz)
        self.rate_hz = 5
        self.timer = self.create_timer(1 / self.rate_hz, self.mock_estop_status)

        self.get_logger().info("Mock Emergency Stop Publisher started.")

    def trigger_succeed(self, request: Trigger.Request, response: Trigger.Response):
        self.get_logger().info("Running trigger")
        time.sleep(0.5)
        response.success = True
        return response

    def trigger_fail(self, request, response: Trigger.Response):
        self.get_logger().info("Running trigger")
        time.sleep(0.5)
        response.success = False
        response.message = "Trigger failed"
        return response

    def mock_estop_status(self):
        """

        Timer callback that updates mock estop status.

        Generates random bool and publishes mock estop status to /emergency_stop topic.

        """
        # Creating and publishing a random Bool message
        msg = Bool()
        msg.data = random.choice([True, False])
        self.publisher.publish(msg)
        self.get_logger().info(f"Published emergency stop: {msg.data}")


def main(args=None):
    rclpy.init(args=args)
    node = MockEstopPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
