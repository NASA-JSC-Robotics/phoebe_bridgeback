from std_msgs.msg import Bool
from rclpy.node import Node
from clearpath_platform_msgs.msg import Status, Power, StopStatus
from sensor_msgs.msg import BatteryState
from geometry_msgs.msg import Twist
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
import rclpy
import sys

import threading

# Basic test program for checking that display state run as expected.
# Run the status node (e.g. phoebe_status_terminal), then run this
# and observe the state changes match the text.


class StateTest(Node):
    def __init__(self, node_name):
        super().__init__(node_name)

        # All of the publications use SensorDataQoS on the C++ side.
        # Set up something equivalent for python
        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )

        self.status_pub = self.create_publisher(Status, "platform/mcu/status", qos)
        self.power_pub = self.create_publisher(Power, "platform/mcu/status/power", qos)
        self.estop_pub = self.create_publisher(Bool, "platform/emergency_stop", qos)
        self.stop_status_pub = self.create_publisher(StopStatus, "platform/mcu/status/stop", qos)
        self.cmd_vel_pub = self.create_publisher(Twist, "platform/cmd_vel_unstamped", qos)
        self.battery_pub = self.create_publisher(BatteryState, "platform/bms/state", qos)

        self.status_msg = Status()
        self.power_msg = Power()
        self.estop_msg = Bool()
        self.stop_status_msg = StopStatus()
        self.cmd_vel_msg = Twist()
        self.battery_msg = BatteryState()

    def test_estopped(self):
        cycle_rate = self.create_rate(2)
        num_cycles = 10

        log = self.get_logger().info
        log("Test Estopped")
        self.estop_msg.data = True
        self.stop_status_msg.needs_reset = True
        # Publish messages in a cycle
        for loop in range(0, num_cycles):
            self.estop_pub.publish(self.estop_msg)
            self.stop_status_pub.publish(self.stop_status_msg)
            cycle_rate.sleep()

        log("Test Estopped with needs reset active")
        self.estop_msg.data = True
        self.stop_status_msg.needs_reset = True
        for loop in range(0, num_cycles):
            self.estop_pub.publish(self.estop_msg)
            self.stop_status_pub.publish(self.stop_status_msg)
            cycle_rate.sleep()

        log("Test Needs Reset with no Estop")
        self.estop_msg.data = False
        self.stop_status_msg.needs_reset = True
        for loop in range(0, num_cycles):
            self.estop_pub.publish(self.estop_msg)
            self.stop_status_pub.publish(self.stop_status_msg)
            cycle_rate.sleep()

        log("Test No Estop")
        self.estop_msg.data = False
        self.stop_status_msg.needs_reset = False
        for loop in range(0, num_cycles):
            self.estop_pub.publish(self.estop_msg)
            self.stop_status_pub.publish(self.stop_status_msg)
            cycle_rate.sleep()

    def test_battery(self):
        cycle_rate = self.create_rate(2)
        num_cycles = 10
        log = self.get_logger().info

        self.battery_msg.voltage = 26.7840982340932
        self.battery_msg.current = 10.10394932

        log("Battery nominal, not charging")
        self.battery_msg.power_supply_health = BatteryState.POWER_SUPPLY_HEALTH_GOOD
        self.battery_msg.percentage = 0.5111111
        self.battery_msg.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_NOT_CHARGING
        for loop in range(0, num_cycles):
            self.battery_pub.publish(self.battery_msg)
            cycle_rate.sleep()

        log("Battery low, not charging")
        self.battery_msg.power_supply_health = BatteryState.POWER_SUPPLY_HEALTH_GOOD
        self.battery_msg.percentage = 0.15689487534
        self.battery_msg.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_NOT_CHARGING
        for loop in range(0, num_cycles):
            self.battery_pub.publish(self.battery_msg)
            cycle_rate.sleep()

        log("Battery nominal, charging")
        self.battery_msg.power_supply_health = BatteryState.POWER_SUPPLY_HEALTH_GOOD
        self.battery_msg.percentage = 0.5
        self.battery_msg.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_CHARGING
        for loop in range(0, num_cycles):
            self.battery_pub.publish(self.battery_msg)
            cycle_rate.sleep()

        log("Battery low, charging")
        self.battery_msg.power_supply_health = BatteryState.POWER_SUPPLY_HEALTH_GOOD
        self.battery_msg.percentage = 0.15
        self.battery_msg.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_CHARGING
        for loop in range(0, num_cycles):
            self.battery_pub.publish(self.battery_msg)
            cycle_rate.sleep()

        log("Battery full, not charging")
        self.battery_msg.power_supply_health = BatteryState.POWER_SUPPLY_HEALTH_GOOD
        self.battery_msg.percentage = 1.0
        self.battery_msg.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_NOT_CHARGING
        for loop in range(0, num_cycles):
            self.battery_pub.publish(self.battery_msg)
            cycle_rate.sleep()

    def test_nominal(self):
        cycle_rate = self.create_rate(2)
        num_cycles = 100
        log = self.get_logger().info

        log("Battery nominal, charging")
        self.battery_msg.power_supply_health = BatteryState.POWER_SUPPLY_HEALTH_GOOD
        self.battery_msg.percentage = 0.5
        self.battery_msg.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_CHARGING
        self.battery_msg.voltage = 27.2
        self.battery_msg.current = 10.10394932
        self.estop_msg.data = False
        self.stop_status_msg.needs_reset = False

        for loop in range(0, num_cycles):
            self.battery_pub.publish(self.battery_msg)
            self.estop_pub.publish(self.estop_msg)
            self.stop_status_pub.publish(self.stop_status_msg)
            self.battery_msg.voltage -= 0.1
            cycle_rate.sleep()


def main():
    rclpy.init()
    test_node = StateTest("state_test")
    thread = threading.Thread(target=rclpy.spin, args=(test_node,), daemon=True)
    thread.start()
    test_node.test_estopped()
    test_node.test_battery()
    #    test_node.test_nominal()
    rclpy.shutdown()
    thread.join()


if __name__ == "__main__":
    main()
