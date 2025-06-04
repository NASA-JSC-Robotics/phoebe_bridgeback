#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
import random


class MockJoystickPublisher(Node):
    def __init__(self):
        super().__init__("mock_joystick_publisher")

        # Publishing to the /emergency_stop topic
        self.publisher = self.create_publisher(Joy, "/joy_teleop/joy", 10)

        # Publishing a new random bool every declared rate (Hz)
        self.rate_hz = 0.5
        self.timer = self.create_timer(1 / self.rate_hz, self.publish_joystick_msg)
        self.num_buttons = 3
        self.num_axes = 3
        self.joystick_msg = Joy(buttons=[0]*self.num_buttons, axes=[0]*self.num_axes)
        self.last_button_index_set = -1
        self.last_axis_index_set = -1

        self.get_logger().info("Mock Joystick Publisher started.")

    def publish_joystick_msg(self):
        """

        Timer callback that updates joystick status

        On each cycle there will be exactly one button pressed, which will be the
        button with index one larger than the button pressed last cycle modulo the
        number of buttons. The button pressed last cycle will be released.
        
        Similarly, on each cycle there will be exactly one axis value set.

        """

        msg = self.joystick_msg                      # Alias for convenience
        msg.buttons[self.last_button_index_set] = 0  # Unpress last button
        
        self.last_button_index_set += 1              # Increment button to set
        if self.last_button_index_set >= self.num_buttons:  # if rollover, reset to 0
            self.last_button_index_set = 0
        msg.buttons[self.last_button_index_set] = 1   # Set button press

        msg.axes[self.last_axis_index_set] = 0        # Unset last axis value
        self.last_axis_index_set += 1
        if self.last_axis_index_set >= self.num_axes:
            self.last_axis_index_set = 0
        msg.axes[self.last_axis_index_set] = random.random()

        # Timestamp message
        current_ros_time = self.get_clock().now()
        msg.header.stamp = current_ros_time.to_msg()

        self.publisher.publish(msg)
        # self.get_logger().info(f"Published emergency stop: {msg.data}")


def main(args=None):
    rclpy.init(args=args)
    node = MockJoystickPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
