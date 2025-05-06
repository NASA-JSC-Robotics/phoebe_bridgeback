#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, String
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup
from controller_manager_msgs.srv import ListControllers
import serial
import time


class PhoebeSafetyManager(Node):
    def __init__(self):
        super().__init__("phoebe_safety_manager")
        # Use ROS 2 parameter system
        arduino_port_param = self.declare_parameter("arduino_port", "/dev/ttyACM0").get_parameter_value().string_value

        # Assign parameters
        self.arduino_port = arduino_port_param

        # Initial states
        self.estop_active = False  # True = safe to enter, False = not safe to enter
        self.controller_active = True  # True = not safe to enter, False = caution

        # Callback group for multithreading
        self.callback_group = ReentrantCallbackGroup()

        # Serial connection to Arduino
        try:
            self.arduino = serial.Serial(self.arduino_port, 9600, timeout=1)
            time.sleep(2)  # Give Arduino time to reset
            self.get_logger().info(f"Connected to Arduino on {self.arduino_port}")
            self.send_light_state(3)  # Default to NOT SAFE
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

        # Create client for controller manager service
        self.controller_client = self.create_client(
            ListControllers, "/controller_manager/list_controllers", callback_group=self.callback_group
        )

        # Timer to check controller status at 5 Hz (every 0.2 seconds)
        self.controller_check_timer = self.create_timer(
            1 / self.rate_hz, self.controllers_are_active, callback_group=self.callback_group
        )

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
        elif self.controller_active:
            msg.data = "NOT_SAFE_TO_ENTER"
            light_state = 3
            color = "\033[91m"  # Red
        else:
            msg.data = "CAUTION"
            light_state = 2
            color = "\033[93m"  # Yellow
        self.publisher.publish(msg)
        self.get_logger().info(f"Published safety status: {color}{msg.data}\033[0m")
        self.send_light_state(light_state)

    def send_light_state(self, state: int):
        """
        Sends a byte to the Arduino to control indicator lights.
        States:
            1 = SAFE (blue)
            2 = CAUTION (yellow)
            3 = NOT SAFE (red)
        Only executes if a serial connection is active.
        """
        if self.arduino and self.arduino.is_open:
            try:
                self.arduino.write(bytes([state]))
                self.get_logger().info(f"Sent light state {state} to Arduino")
            except serial.SerialException as e:
                self.get_logger().error(f"Failed to send to Arduino: {e}")

    def controllers_are_active(self):
        """
        Calls the controller manager to determine if any controllers are active.
        Uses a non-blocking async service call with a done callback.
        """
        if self.controller_client.service_is_ready():
            request = ListControllers.Request()
            future = self.controller_client.call_async(request)
            future.add_done_callback(self.controller_response)
        else:
            self.get_logger().warn("Controller manager service not available.")

    def controller_response(self, future):
        """
        Callback to process the result of the controller manager service call.
        Updates internal controller_active state.
        """
        try:
            response = future.result()
            self.controller_active = any(
                c.state == "active" and len(c.required_command_interfaces) > 0 for c in response.controller
            )
            for (
                ctrl
            ) in response.controller:  # Print for troubleshooting. Making sure it's publishing states accordingly.
                print(f"Controller name: {ctrl.name}")
                print(f"Controller state: {ctrl.state}")
                print(f"Controller's commands if any: {ctrl.required_command_interfaces}")
            self.get_logger().info(f"Controller active? {self.controller_active}")
        except Exception as e:
            self.get_logger().warn(f"Failed to get controller status: {e}")
            self.controller_active = False


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
