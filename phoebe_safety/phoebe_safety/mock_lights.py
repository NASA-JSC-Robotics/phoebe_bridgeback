import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class MockLights(Node):
    def __init__(self):
        super().__init__("mock_lights")
        
        # Subscribing to /safety_status topic
        self.subscription = self.create_subscription(String, "/safety_status", self.safety_status_callback, 10)

        # Rate
        self.rate_hz = 5
        self.timer = self.create_timer(1 / self.rate_hz, self.light_message)

        self.get_logger().info("Mock Lights on.")

    # Callbacks
    def safety_status_callback(self, msg: String):
        """

        Callback for the /safety_status topic.
 
        Updates safety state. 

        """
        self.safety_status_callback = msg.data
        self.get_logger().info(f"Status? {self.safety_status_callback}")

    def light_message(self):
        """

        Timer callback that updates light color according to safety state.

        Prints light color message.

        """
        if self.safety_status_callback == "SAFE_TO_ENTER":
            light_message = "BLUE LIGHT"
            color = "\033[94m"  # Blue
        else:
            light_message = "RED LIGHT"
            color = "\033[91m"  # Red

        self.get_logger().info(f"{color}{light_message}\033[0m")


def main(args=None):
    rclpy.init(args=args)
    node = MockLights()

    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
