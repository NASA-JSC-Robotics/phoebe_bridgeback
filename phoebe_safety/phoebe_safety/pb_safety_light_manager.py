#!/usr/bin/env python3
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

        # Use ROS 2 parameter system
        arduino_port_param = self.declare_parameter("arduino_port", "/dev/ttyACM0").get_parameter_value().string_value

        # Assign parameters
        self.arduino_port = arduino_port_param

        # Internal state of estop
        self.estop_active = False  # True = safe to enter, False = not safe to enter

        # Callback group for multithreading
        self.callback_group = ReentrantCallbackGroup()

        # Serial connection to Arduino
    
        try:
            self.arduino = serial.Serial(self.arduino_port, 9600, timeout=1)
            time.sleep(2)  # Give Arduino time to reset
            self.get_logger().info(f"Connected to Arduino on {self.arduino_port}")
            self.send_light_state()  # Will default to "not safe"
        except serial.SerialException as e:
            self.arduino = None
            self.get_logger().warn(f"Could not connect to Arduino: {e}")

        # Subscribing to estop topic
        self.subscription = self.create_subscription(
            Bool, "/emergency_stop", self.estop_callback, 10, callback_group=self.callback_group
        )

        # Publishing to "safety_status" topic
        self.publisher = self.create_publisher(String, "/safety_status", 10, callback_group=self.callback_group)

        # Timer
        self.rate_hz = 5
        self.timer = self.create_timer(1 / self.rate_hz, self.check_system_safety, callback_group=self.callback_group)

        # Logger
        self.get_logger().info(f"This node has started: {self.get_name()}")

    def estop_callback(self, msg: Bool):
        """

        Callback for the /emergency_stop topic.

        True = active. False = not active.

        Updates state of emergency stop signal.

        """
        self.get_logger().info("E-stop callback triggered")
        self.estop_active = msg.data
        self.get_logger().info(f"E-stop active? {self.estop_active}")

    def check_system_safety(self):
        """

        Timer callback that evaluates system safety status.

        Publishes current safety status and updates light indicators.

        """
        msg = String()
        if self.estop_active:
            msg.data = "SAFE_TO_ENTER"
            light_state = 1  
            color = "\033[94m"  # Blue
        else:
            msg.data = "NOT_SAFE_TO_ENTER"
            light_state = 3  
            color = "\033[91m"  # Red
            
        self.publisher.publish(msg)
        self.get_logger().info(f"Published safety status: {color}{msg.data}\033[0m")
        self.send_light_state(light_state)

    def send_light_state(self, state: int):
        """

        Sends a byte to the Arduino to control indicator lights.

        State 1 = SAFE (blue), State 3 = NOT SAFE (red).

        Only executes if a serial connection is active.

        """
        if self.arduino and self.arduino.is_open:
            try:
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
