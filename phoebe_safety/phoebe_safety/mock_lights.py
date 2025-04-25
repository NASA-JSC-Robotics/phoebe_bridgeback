import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.executors import MultiThreadedExecutor


class MockLights(Node):
    def __init__(self):
        super().__init__("mock_lights")


        # Subscribing to /safety_status topic
        self.subscription = self.create_subscription(String, "/safety_status", self.safety_status_callback, 10)

        # Publishing to the /mock_lights topic
        self.publisher = self.create_publisher(String, "/mock_lights", 10)

        # Publishing a new random bool every declared rate (Hz)
        self.rate_hz = 0.5  # Chose a somewhat slower rate to be realistic (Same as e-stop)
        self.timer = self.create_timer(1 / self.rate_hz, self.timer_callback)

        self.get_logger().info("Mock Lights on.")

   # Callbacks
    def safety_status_callback(self, msg: String):
        self.safety_status_callback= msg.data
        self.get_logger().info(f"Status? {self.safety_status_callback}")

    def timer_callback(self):
        msg = String()
    
        if self.safety_status_callback == "SAFE_TO_ENTER":
            msg.data = "BLUE LIGHT"
            color = "\033[94m"  # Blue
        else:
            msg.data = "RED LIGHT"
            color = "\033[91m"  # Red
    
        self.publisher.publish(msg)
        self.get_logger().info(f"{color}{msg.data}\033[0m") 

def main(args=None):
    rclpy.init(args=args)
    node = MockLights()
   
    # Establishing a MultiThreadedExecutor to run callbacks concurrently
    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()