#!/usr/bin/env python3
#
# Simple node that implements system actions based on joystick state.
# Actions are read from a configuration file, specified using the
# parameter "actions_file."
# 
# For joystick button and axis values used here, see https://github.com/ros-drivers/joystick_drivers/tree/ros2/joy
# 
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from rcl_interfaces.msg import ParameterDescriptor
import yaml
import math

class ButtonAction(object):
    def __init__(self, dict):
        self.button: int = dict['button']
        self.action: str = dict['action']

class AxisAction(object):
    def __init__(self, dict):
        self.axis:   int = dict['axis']
        self.action: str = dict['action']


class PhoebeJoystickSafing(Node):
    def __init__(self):
        super().__init__("phoebe_joystick_safing")

        # Subscribe to joystick topic
        self.subscription = self.create_subscription(
            Joy, "/joy_teleop/joy", self.joy_callback, 10
        )

        # Grab config file
        self.declare_parameter('actions_file', '', ParameterDescriptor(description='Path to the actions file.'))
        self.declare_parameter('axis_tolerance', 0.01, ParameterDescriptor(description='How much motion on an axis consitutes "movement."'))

        actions_file = self.get_parameter('actions_file').value
        self.get_logger().info(f"Joystick Safing node running from actions in {actions_file}")
        self.button_actions, self.axis_actions = self.read_actions_from_file(actions_file)
        self.previous_state: Joy = None
        self.axis_tolerance = self.get_parameter('axis_tolerance').value

    def get_validated_action(self, action):
        if hasattr(self, action) and callable(getattr(self, action)):
            return getattr(self, action)
        elif action in globals() and callable(globals()[action]):
            return globals()[action]
        else:
            return None

    def read_actions_from_file(self, actions_file: str):
        button_actions = {}  # A dict of button number -> list of actions
        axis_actions   = {}
        try:
            with open(actions_file) as actions_file_stream:
                actions_content = yaml.safe_load(actions_file_stream)

                for thing in actions_content:
                    self.get_logger().warn("Got: " + str(thing))

                if 'button_actions' in actions_content:
                    for action in actions_content['button_actions']:
                        action_config = ButtonAction(action)
                        method = self.get_validated_action(action_config.action)
                        if not method:
                            self.get_logger().error(f"Unknown action: {action_config.action}")
                            continue

                        if action_config.button not in button_actions:
                            button_actions[action_config.button] = []
                        button_actions[action_config.button].append(method)

                if 'axis_actions' in actions_content:
                     for action in actions_content['axis_actions']:
                        action_config = AxisAction(action)
                        method = self.get_validated_action(action_config.action)
                        if not method:
                            self.get_logger().error(f"Unknown action: {action_config.action}")
                            continue

                        if action_config.axis not in axis_actions:
                            axis_actions[action_config.axis] = []
                        axis_actions[action_config.axis].append(method)

        except FileNotFoundError:
            self.get_logger().fatal(f"Cannot open actions config file: {actions_file}")
        except yaml.YAMLError as e:
            self.get_logger().fatal(f"Unable to parse actions file {actions_file}: {e}")
        # except Exception as e:
        #     self.get_logger().error(f"Unknown error: {e}")

        return button_actions, axis_actions
    
    def print_value(self, axis_index: int, msg: Joy):
        self.get_logger().info(f"Value of axis {axis_index} is {msg.axes[axis_index]}")

    def print_hello(self, button_index: int, msg: Joy):
        self.get_logger().info("Hello")

    def toggle_controller_state(self, button_index: int, msg: Joy):
        self.get_logger().info(f"Toggling controller state from button {button_index}")

    def run_action(self, action, button_index: int, msg: Joy):
        action(button_index, msg)
    
    def joy_callback(self, msg: Joy):
        # For the first message, there is nothing to compare against, so store state and return
        if self.previous_state is None:
            self.previous_state = msg
            return

        # Check for changes
        num_buttons = len(msg.buttons)
        assert(num_buttons == len(self.previous_state.buttons))
        buttons_activated = [ index for index in range(0,len(msg.buttons)) 
                             if self.previous_state.buttons[index] == 0 and msg.buttons[index] == 1 ]
        # Loop through the activated buttons. If there are associated actions, run them
        for button_index in buttons_activated:
            if button_index in self.button_actions:
                for action in self.button_actions[button_index]:
                    self.run_action(action, button_index, msg)

        # Check for changes
        num_axes = len(msg.axes)
        assert(num_axes == len(self.previous_state.axes))
        axes_activated = [ index for index in range(0,len(msg.axes)) 
                             if math.fabs(msg.axes[index]-self.previous_state.axes[index]) > self.axis_tolerance ]
        # Loop through the activated axes. If there are associated actions, run them
        for axis_index in axes_activated:
            if axis_index in self.axis_actions:
                for action in self.axis_actions[axis_index]:
                    self.run_action(action, axis_index, msg)


        self.previous_state = msg

def main(args=None):
    rclpy.init(args=args)      
    joystick_safing_node = PhoebeJoystickSafing()
    try:
        rclpy.spin(joystick_safing_node)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()