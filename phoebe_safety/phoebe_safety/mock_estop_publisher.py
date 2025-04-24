import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
import random


class MockEstopPublisher(Node):
    def __init__(self):
        super().__init__('mock_estop_publisher')

        # Publishing to the /emergency_stop topic
        self.publisher = self.create_publisher(Bool, '/emergency_stop', 10)

        # Publishing a new random bool every decalred rate (Hz)
        self.rate_hz = 0.5 # Chose a somewhat slower rate to be realistic
        self.timer = self.create_timer(1 / self.rate_hz, self.timer_callback)

        self.get_logger().info('Mock Emergency Stop Publisher started.')

    def timer_callback(self):
        # Creating and publishing a random Bool message
        msg = Bool()
        msg.data = random.choice([True, False])
        self.publisher.publish(msg)
        self.get_logger().info(f'Published emergency stop: {msg.data}')


def main(args=None):
    rclpy.init(args=args)
    node = MockEstopPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()