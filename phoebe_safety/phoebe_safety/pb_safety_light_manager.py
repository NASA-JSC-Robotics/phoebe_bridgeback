import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, String
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup
import serial
import time
 
 
class PhoebeSafetyManager(Node):
    def __init__(self):
        super().__init__("phoebe_safety_manager")
 
        # Use ROS 2 parameter system for `use_mock_lights` flag
        use_mock_lights_param = self.declare_parameter("use_mock_lights", False).get_parameter_value().bool_value
 
        # Internal state of estop
        self.estop_active = False  # True = safe to enter, False = not safe to enter
 
        # For mock lights (sim)
        self.use_mock_lights = use_mock_lights_param
 
        # Callback group for multithreading
        self.callback_group = ReentrantCallbackGroup()
 
        # Serial connection to Arduino
        if self.use_mock_lights:
            self.get_logger().info("Simulation only. Using mock lights, no Arduino required.")
            self.arduino = None
        else:
            try:
                self.get_logger().info("Not a simulation. Using real lights. Plug in Arduino.")
                self.arduino = serial.Serial("/dev/ttyACM0", 9600, timeout=1)
                time.sleep(2)  # Give Arduino time to reset
                self.get_logger().info("Connected to Arduino on /dev/ttyACM0")
                self.send_light_state()  # Will default to "not safe"
            except serial.SerialException as e:
                self.arduino = None
                self.get_logger().warn(f"Could not connect to Arduino: {e}")
 
        # Subscribing to estop topic
        self.subscription = self.create_subscription(
            Bool,
            "/emergency_stop",
            self.estop_callback,
            10,
            callback_group=self.callback_group
        )
 
        # Publishing to "safety_status" topic
        self.publisher = self.create_publisher(
            String,
            "/safety_status",
            10,
            callback_group=self.callback_group
        )
 
        # Timer
        self.rate_hz = 5
        self.timer = self.create_timer(
            1 / self.rate_hz,
            self.timer_callback,
            callback_group=self.callback_group
        )
 
        # Logger
        self.get_logger().info("Phoebe Safety Manager Node has started")
 
    def estop_callback(self, msg: Bool):
        self.get_logger().info("E-stop callback triggered")
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
        self.send_light_state()
 
 
    def send_light_state(self):
        if self.arduino and self.arduino.is_open:
            try:
                state = 1 if self.estop_active else 3
                self.arduino.write(bytes([state]))
                self.get_logger().info(f"Sent light state {state} to Arduino")
            except serial.SerialException as e:
                self.get_logger().error(f"Failed to send to Arduino: {e}")
 
 
def main(args=None):
    rclpy.init(args=args)
 
    node = PhoebeSafetyManager()
 
    executor = MultiThreadedExecutor()
    executor.add_node(node)
 
    try:
        executor.spin()
    finally:
        if node.arduino:
            node.arduino.close()
        node.destroy_node()
        rclpy.shutdown()
 
 
if __name__ == "__main__":
    main()