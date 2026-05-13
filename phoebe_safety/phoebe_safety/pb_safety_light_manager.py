#!/usr/bin/env python3
#
# Copyright (c) 2025, United States Government, as represented by the
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
from std_msgs.msg import Bool
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup
from controller_manager_msgs.srv import ListControllers
from phoebe_interfaces.msg import SafetyStatus
from phoebe_interfaces.msg import SafetyCurrent
from phoebe_interfaces.msg import SafetyRawVoltages
import serial
import time
import struct
import yaml
from rclpy.qos import QoSProfile, ReliabilityPolicy
import datetime
from enum import IntEnum


class LightColor(IntEnum):
    RED = 1
    YELLOW = 2
    BLUE = 3


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
            self.declare_parameter("arduino_port", "/dev/ttyACM0").get_parameter_value().string_value
        )

        self.sensor_config_file = (
            self.declare_parameter("current_sensor_config_file").get_parameter_value().string_value
        )

        # Assign parameters
        self.arduino_port = arduino_port_param

        # E stop subscription topic name
        self.estop_topic = "ridgeback/platform/emergency_stop"

        # Safety status publisher topic name
        self.safety_status_topic = "safety_status"

        # Safety raw voltages publisher topic name
        self.safety_raw_voltages_topic = "safety_raw_voltages"

        # Safety current publisher topic name
        self.safety_current_topic = "safety_current"

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

        # Publishing to "safety_current" topic with the custom SafetyCurrent message
        self.current_publisher = self.create_publisher(
            SafetyCurrent, self.safety_current_topic, 10, callback_group=self.callback_group
        )

        # Publishing to "safety_raw_voltages" topic with the custom SafetyRawVoltages message
        self.raw_voltages_publisher = self.create_publisher(
            SafetyRawVoltages, self.safety_raw_voltages_topic, 10, callback_group=self.callback_group
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

        # Set up sensors from sensor config file
        self.current_msg = SafetyCurrent()
        self.raw_voltages_msg = SafetyRawVoltages()
        self.setup_sensors(self.sensor_config_file)

    def setup_sensors(self, config_file):
        # Read the sensor config file and parse the content it contains into member variables
        try:
            with open(config_file) as stream:
                content = yaml.safe_load(stream)

                self.sensors = content["sensors"]

                # sensor_config = content["sensors"]
                # self.voltage_offsets = sensor_config["voltage_offsets"]
                # self.sensitivity = sensor_config["sensitivity"]
                # self.is_valid = sensor_config["is_valid"]

                # self.get_logger().info(f"Read sensor voltage offsets: {self.voltage_offsets}")
                # self.get_logger().info(f"Read sensor sensitivity: {self.sensitivity}")
                # self.get_logger().info(f"Read sensor validity: {self.is_valid}")
                self.get_logger().info(f"Read sensor configs: {self.sensors}")

        except FileNotFoundError:
            self.get_logger().fatal(f"Cannot open sensor config file: {self.sensor_config_file}")
        except yaml.YAMLError as e:
            self.get_logger().fatal(f"Unable to parse sensor config file {self.sensor_config_file}: {e}")

        # Check arrays have the same number of values

        if len(self.sensors) != self.raw_voltages_msg.NUM_FIRMWARE_VALUES:
            self.get_logger.fatal(f"Sensor config has {len(self.sensors)} values but the SafetyRawVoltages "
                                  "value says there should be {self.raw_voltages_msg.NUM_FIRMWARE_VALUES}")

        # Names and validity won't change, so prefill them
        self.current_msg.names = [sensor["name"] for sensor in self.sensors]
        self.raw_voltages_msg.names = self.current_msg.names

        self.current_msg.is_valid = [sensor["is_valid"] for sensor in self.sensors]
        self.raw_voltages_msg.is_valid = self.current_msg.is_valid

    def estop_callback(self, msg: Bool):
        """
        Callback for the /emergency_stop topic.
        True = active. False = not active.
        Updates state of emergency stop signal.
        """
        if not self.arduino_connected:
            self.try_reconnect_arduino()
            return

        self.get_logger().debug("E-stop callback triggered")
        self.estop_active = msg.data
        self.last_estop_msg_time = datetime.datetime.now()
        self.get_logger().debug(f"E-stop active? {self.estop_active}")

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
            self.get_logger().debug("No estop message received recently. Assuming NOT safe.")
            self.estop_active = False

        msg = SafetyStatus()  # Custom SafetyStatus message

        if self.estop_active:
            msg.status = SafetyStatus.SAFE_TO_ENTER
            light_state = LightColor.RED
        elif self.controller_active:
            msg.status = SafetyStatus.NOT_SAFE_TO_ENTER
            light_state = LightColor.BLUE
        else:
            msg.status = SafetyStatus.CAUTION
            light_state = LightColor.YELLOW

        color = color_map[light_state]
        msg.timestamp = self.get_clock().now().to_msg()  # Added timestamp
        self.publisher.publish(msg)
        self.get_logger().debug(
            f"Published safety status: {color}{status_descriptions[msg.status]}\033[0m At time {msg.timestamp}"
        )

        self.send_light_state(light_state)
        self.read_currents()

    def publish_not_safe(self):
        """
        Publishes NOT SAFE safety status.
        """
        msg = SafetyStatus()
        msg.status = SafetyStatus.NOT_SAFE_TO_ENTER
        light_state = LightColor.BLUE
        color = color_map[light_state]
        msg.timestamp = self.get_clock().now().to_msg()  # Added timestamp
        self.publisher.publish(msg)

        self.get_logger().debug(
            f"Published safety status: {color}{status_descriptions[msg.status]}\033[0m At time {msg.timestamp}"
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
            self.get_logger().debug(f"Connected to Arduino on {self.arduino_port}")
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
                self.get_logger().debug(f"Sent light state {state} to Arduino")
            except Exception as e:
                self.get_logger().error(f"Failed to send to Arduino: {e}")
                self.arduino_connected = False
                self.arduino = None
                self.publish_not_safe()

    def read_currents(self):
        if self.arduino and self.arduino.is_open:
            buf_size = self.arduino.in_waiting
            finish = True
            while finish:
                if buf_size != 0:
                    dummy = self.arduino.read(1)
                    buf_size = buf_size - 1
                    if dummy[0] == 35 and buf_size != 0:
                        dummy1 = self.arduino.read(1)
                        buf_size = buf_size - 1
                        if dummy1[0] == 35 and buf_size >= 40:
                            for id in range(self.raw_voltages_msg.NUM_FIRMWARE_VALUES):
                                # Must read regardless of whether the reading is valid
                                raw_value = struct.unpack('<f', self.arduino.read(4))[0]
                                if self.raw_voltages_msg.is_valid[id]:
                                    self.raw_voltages_msg.voltages[id] = raw_value
                                else:
                                    self.raw_voltages_msg.voltages[id] = 0.0
                                self.current_msg.currents[id] = \
                                    self.compute_current(id, self.raw_voltages_msg.voltages[id])

                            # Set timestamp and publish messages
                            self.raw_voltages_msg.timestamp = self.get_clock().now().to_msg()
                            self.current_msg.timestamp = self.raw_voltages_msg.timestamp
                            self.current_publisher.publish(self.current_msg)
                            self.raw_voltages_publisher.publish(self.raw_voltages_msg)

                            buf_size = buf_size - 40
                        else:
                            finish = False
                else:
                    finish = False

    def compute_current(self, index, voltage):
        """
        Compute current for the index'th sensor based on empirical values from testing
        The approach is described for this board at: https://www.pololu.com/product/5355
        """
        return (voltage - self.sensors[index]["voltage_offset"]) / self.sensors[index]["sensitivity"]

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
            self.get_logger().debug("Controller manager service not available.")
            self.controller_manager_check()
            current_time = datetime.datetime.now()
            if self.last_cm_stamp is None or (current_time - self.last_cm_stamp).total_seconds() > self.wait_time:
                self.get_logger().debug("Controller manager service was not found. No controllers are active.")
                self.controller_active = False
            else:
                self.get_logger().debug(
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
                if (
                    ctrl.state == "active"
                    and len(ctrl.required_command_interfaces) > 0
                    and ctrl.type not in self.controller_whitelist
                ):
                    self.controller_active = True
                    break

            self.get_logger().debug(f"Is there an unsafe controller active? {self.controller_active}")

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
