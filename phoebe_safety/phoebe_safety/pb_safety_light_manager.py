import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, String

# from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor


class PhoebeSafetyManager(Node):
    def __init__(self):
        super().__init__("phoebe_safety_manager")

        # Internal state of estop
        self.estop_active = False  # True = safe to enter, False = not safe tp enter

        # Subscribing to estop topic
        self.subscription = self.create_subscription(Bool, "/emergency_stop", self.estop_callback, 10)

        # Publishing to "safety_status" topic which publishes the current safety state.
        self.publisher = self.create_publisher(String, "/safety_status", 10)

        # Timer
        self.rate_hz = 5
        self.timer = self.create_timer(1 / self.rate_hz, self.timer_callback)

        # Logger
        self.get_logger().info("Phoebe Safety Manager Node has started")

    # Callbacks
    def estop_callback(self, msg: Bool):
        self.estop_active = msg.data
        self.get_logger().info(f"E-stop active? {self.estop_active}")

    def timer_callback(self):
        msg = String()

        if self.estop_active:
            msg.data = "SAFE_TO_ENTER"
        else:
            msg.data = "NOT_SAFE_TO_ENTER"

        self.publisher.publish(msg)
        self.get_logger().info(f"Published safety status: {msg.data}")


def main(args=None):
    rclpy.init(args=args)
    node = PhoebeSafetyManager()

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
