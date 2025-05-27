#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup
from controller_manager_msgs.srv import ListControllers
from phoebe_interfaces.msg import SafetyStatus 
import serial
import time
from rclpy.qos import QoSProfile, ReliabilityPolicy
import datetime
from datetime import timezone
from zoneinfo import ZoneInfo
from enum import IntEnum


class LightColor(IntEnum):
    BLUE = 1
    YELLOW = 2
    RED = 3


status_descriptions = {
    SafetyStatus.SAFE_TO_ENTER: "SAFE to enter the environment.",
    SafetyStatus.CAUTION: "CAUTION. Not estopped, but no active (unsafe) controllers.",
    SafetyStatus.NOT_SAFE_TO_ENTER: "NOT SAFE to enter.",
}

color_map = {LightColor.BLUE: "\033[94m", LightColor.YELLOW: "\033[93m", LightColor.RED: "\033[91m"}


class PhoebeSafetyManager(Node):
    def __init__(self, sim_arduino=False):
        super().__init__("phoebe_safety_manager")
        self.sim_arduino = sim_arduino

        # Use ROS 2 parameter system
        arduino_port_param = (
            self.declare_parameter("arduino_port", "/dev/safety_light").get_parameter_value().string_value
        )

        # Assign parameters
        self.arduino_port = arduino_port_param

        # E stop subscription topic name
        self.estop_topic = "ridgeback/platform/emergency_stop"

        # Safety status publisher topic name
        self.safety_status_topic = "safety_status"

        # Service for listing controllers from the controller manager
        self.list_controllers_srv = "controller_manager/list_controllers"

        # Initial states
        self.estop_active = False  # True = safe to enter, False = not safe to enter
        self.controller_active = True  # True = not safe to enter, False = caution

        # Callback group for multithreading
        self.callback_group = ReentrantCallbackGroup()

        # Serial connection to Arduino
        self.baud_rate = 9600
        self.arduino = None
        self.arduino_connected = False

        # Wait time for checks (Seconds)
        self.wait_time = 5

        while not self.arduino_connected and rclpy.ok():
            self.try_reconnect_arduino()

        # Subscribing to estop topic
        qos_profile = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT, depth=10)
        self.subscription = self.create_subscription(
            Bool, self.estop_topic, self.estop_callback, qos_profile, callback_group=self.callback_group
        )
        self.last_estop_msg_time = datetime.datetime.now()
        # Publishing to "safety_status" topic with the custom SafetyStatus message
        self.publisher = self.create_publisher(
            SafetyStatus, self.safety_status_topic, 10, callback_group=self.callback_group
        )

        # Timer to check system s￼tatus at 5 Hz (every 0.2 seconds)
        self.rate_hz = 5
        self.timer = self.create_timer(1 / self.rate_hz, self.check_system_safety, callback_group=self.callback_group)

        # Create client for controller manager service
        self.controller_client = self.create_client(
            ListControllers, self.list_controllers_srv, callback_group=self.callback_group
        )

        # Timer to check controller status at 5 Hz (every 0.2 seconds)
        self.controller_check_timer = self.create_timer(
            1 / self.rate_hz, self.controllers_are_active, callback_group=self.callback_group
        )

        self.controller_manager_check_timer = self.create_timer(
            1 / self.rate_hz, self.controller_manager_check, callback_group=self.callback_group
        )
        self.last_cm_stamp = None

        # Controller Whitelist - if active, still safe
        self.controller_whitelist = ["ur_controllers/FreedriveModeController"]  # Can add more to list if needed later

        # Logger
        self.get_logger().info(f"This node has started: {self.get_name()}")

    def format_timestamp_cst(self, time_msg):
        total_seconds = time_msg.sec + time_msg.nanosec / 1e9
        dt_utc = datetime.datetime.fromtimestamp(total_seconds, tz=timezone.utc)
        dt_cst = dt_utc.astimezone(ZoneInfo("America/Chicago"))
        return dt_cst.strftime("%m-%d-%Y %I:%M:%S.%f %p %Z.")

    def estop_callback(self, msg: Bool):
        """
        Callback for the /emergency_stop topic.
        True = active. False = not active.
        Updates state of emergency stop signal.
        """
        if not self.arduino_connected:
            self.try_reconnect_arduino()
            return

        self.get_logger().info("E-stop callback triggered")
        self.estop_active = msg.data
        self.last_estop_msg_time = datetime.datetime.now()
        self.get_logger().info(f"E-stop active? {self.estop_active}")

    def check_system_safety(self):
        """
        Timer callback that evaluates system safety status.
        Publishes current safety status and updates light indicators.
        """
        if not self.arduino_connected:
            self.try_reconnect_arduino()
            return
        current_time = datetime.datetime.now()
        if (current_time - self.last_estop_msg_time).total_seconds() > self.wait_time:
            self.get_logger().warn("No estop message received recently. Assuming NOT safe.")
            self.estop_active = False

        msg = SafetyStatus()  # Custom SafetyStatus message

        if self.estop_active:
            msg.status = SafetyStatus.SAFE_TO_ENTER
            light_state = LightColor.BLUE
        elif self.controller_active:
            msg.status = SafetyStatus.NOT_SAFE_TO_ENTER
            light_state = LightColor.RED
        else:
            msg.status = SafetyStatus.CAUTION
            light_state = LightColor.YELLOW

        color = color_map[light_state]
        msg.timestamp = self.get_clock().now().to_msg()  # Added timestamp
        self.publisher.publish(msg)
        formatted_time = self.format_timestamp_cst(msg.timestamp)
        self.get_logger().info(
            f"Published safety status: {color}{status_descriptions[msg.status]}\033[0m At time {formatted_time}"
        )

        self.send_light_state(light_state)

    def publish_not_safe(self):
        """
        Publishes NOT SAFE safety status.
        """
        msg = SafetyStatus()
        msg.status = SafetyStatus.NOT_SAFE_TO_ENTER
        light_state = LightColor.RED
        color = color_map[light_state]
        msg.timestamp = self.get_clock().now().to_msg()  # Added timestamp
        self.publisher.publish(msg)
        formatted_time = self.format_timestamp_cst(msg.timestamp)

        self.get_logger().info(
            f"Published safety status: {color}{status_descriptions[msg.status]}\033[0m At time {formatted_time}"
        )

    def try_reconnect_arduino(self):
        """
        Tries to reconnect with Arduino if disconnected.
        """
        if self.sim_arduino:
            self.arduino_connected = True
            return

        try:
            self.arduino = serial.Serial(self.arduino_port, self.baud_rate, timeout=1)
            time.sleep(2)
            self.arduino_connected = True
            self.get_logger().info(f"Reconnected to Arduino on {self.arduino_port}")
            self.send_light_state(LightColor.RED)
        except Exception as e:
            self.get_logger().warn(f"Arduino connection LOST. Need to reconnect: {e}")

    def send_light_state(self, state: LightColor):
        """
        Sends a byte to the Arduino to control indicator lights.
        Only executes if a serial connection is active.
        """
        if self.arduino and self.arduino.is_open:
            try:
                self.arduino.write(bytes([state]))
                self.get_logger().info(f"Sent light state {state} to Arduino")
            except Exception as e:
                self.get_logger().error(f"Failed to send to Arduino: {e}")
                self.arduino_connected = False
                self.arduino = None
                self.publish_not_safe()

    def controller_manager_check(self):
        node_names = self.get_node_names_and_namespaces()
        for name in node_names:
            self.get_logger().debug(f"name: {name} ")
            if "controller_manager" in name:
                self.last_cm_stamp = datetime.datetime.now()

    def controllers_are_active(self):
        """
        Calls the controller manager to determine if any controllers are active.
        Uses a non-blocking async service call with a done callback.
        """
        if not self.arduino_connected:
            self.try_reconnect_arduino()
            return

        time_out = 1

        if self.controller_client.wait_for_service(time_out):
            request = ListControllers.Request()
            future = self.controller_client.call_async(request)
            future.add_done_callback(self.controller_response)
        else:
            self.get_logger().warn("Controller manager service not available.")
            self.controller_manager_check()
            current_time = datetime.datetime.now()
            if self.last_cm_stamp is None or (current_time - self.last_cm_stamp).total_seconds() > self.wait_time:
                self.get_logger().info("Controller manager service was not found. " "No controllers are active.")
                self.controller_active = False
            else:
                self.get_logger().info(
                    "Controller_manager node was seen within the last 5 seconds, "
                    "but the list controllers service is unavailable."
                )
                self.controller_active = True  # Something weird. Assume not safe.

    def controller_response(self, future):
        """
        Callback to process the result of the controller manager service call.
        Updates internal controller_active state.
        """
        try:
            response = future.result()

            self.controller_active = False
            for ctrl in response.controller:
                self.get_logger().debug(f"Controller name: {ctrl.name}")
                self.get_logger().debug(f"Controller state: {ctrl.state}")
                self.get_logger().debug(f"Controller's commands if any: {ctrl.required_command_interfaces}")
                if ctrl.state == "active" and len(ctrl.required_command_interfaces) > 0 and ctrl.type not in self.controller_whitelist:
                    self.controller_active = True
                    break

            self.get_logger().info(f"Is there an unsafe controller active? {self.controller_active}")

        except Exception as e:
            self.get_logger().warn(f"Failed to get controller status: {e}")
            self.controller_active = True  # Not safe.


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
