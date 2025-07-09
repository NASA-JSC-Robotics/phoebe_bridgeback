#!/usr/bin/env python3
#
# Simple node that implements system actions based on joystick state.
# Actions and bindings are read from a configuration file, specified using the
# parameter "actions".
#
# For joystick button and axis values used here, see https://github.com/ros-drivers/joystick_drivers/tree/ros2/joy
#
import rclpy
from rclpy.node import Node
from rclpy.client import Client
from rclpy.task import Future
from sensor_msgs.msg import Joy
from rcl_interfaces.msg import ParameterDescriptor
from std_srvs.srv import Trigger
from functools import partial
import abc
import yaml
import math


# Abstract parent class for actions
class RunnableAction:
    def __init__(self):
        super().__init__()

    @abc.abstractmethod
    def run_action(self, button_index: int, msg: Joy) -> None:
        return


# A service action (i.e. service call with no parameters)
class ServiceAction(RunnableAction):
    current_request_id = 0

    def __init__(self, service_name: str, node: Node):
        """Constructor

        Args:
            service_name (str): Name of the service to run

        It would be a little faster to construct the service client in the constructor, but:
        1. The service may not exist when this node is being spun up, but may exist by the time it is
        triggered, and
        2. For a given configuration, the service may never be triggered
        So we adopt a lazy initialization approach and connect the client on first call.
        """
        super().__init__()
        self.service_name = service_name
        self.client: Client = node.create_client(Trigger, service_name)
        self.request = Trigger.Request()
        self.node = node
        self.future = None

    def run_action(self, button_index: int, msg: Joy) -> None:
        """Run a defined action

        Args:
            button_index (int): index of the button generating the action
            msg (Joy): joystick input message

        Handling service calls in ROS2 is complex. In our case, the services are triggers, so the status will
        be simply "succeeded" or "failed." There's not much we'd want to do here in the case of failure
        beyond status that, so the approach is to keep it simple, run the service asynchronously and
        report on the result. Request ids are added in case we need to identify requests.
        """
        self.node.get_logger().info(f"Attempting to reach {self.service_name}")
        if not self.client.wait_for_service(timeout_sec=1):
            self.node.get_logger().error(f"Unable to call service {self.service_name}: service is unavailable")
            return False
        self.node.get_logger().info(f"Calling service {ServiceAction.current_request_id}: {self.service_name}")
        self.future = self.client.call_async(self.request)
        self.future.add_done_callback(partial(self._receive_response, request_id=ServiceAction.current_request_id))
        ServiceAction.current_request_id += 1

    def _receive_response(self, future: Future, request_id: int) -> None:
        """Status function for service execution

        Args:
            future (Future): Value of the completed future
            request_id (int): Request id (specified when the service is run)

        """
        result: Trigger.Response = future.result()
        if not result.success:
            self.node.get_logger().error(
                f"Service request {request_id} to service {self.service_name} failed: {result.message}"
            )
        else:
            self.node.get_logger().info(f"Service request {request_id} to service  {self.service_name} succeeded")
        self.future = None


# Action to call a function. This is most likely useful for debug, since the options
# are limited to calling functions that don't need parameters and are either
# globally available or supported by the node.
class FunctionAction(RunnableAction):
    def __init__(self, function_name: str, node: Node):
        """Constructor

        Args:
            function_name (str): name of the function to call
            node (Node): supporting node
        """
        super().__init__()
        self.function_name = function_name
        self.node = node
        self.functor = self.get_validated_action(function_name)
        if self.functor is None:
            raise RuntimeError(f"Cannot find a way to execute {function_name}")

    def get_validated_action(self, function_name: str) -> any:
        """Find a function corresponding to the given function name.

        Args:
            function_name (str): name of the function to find
            node (Node): supporting node

        Returns:
            any: None, if no function is found, or the functor
        """
        if self.node is not None and hasattr(self.node, function_name) and callable(getattr(self.node, function_name)):
            return getattr(self.node, function_name)
        elif function_name in globals() and callable(globals()[function_name]):
            return globals()[function_name]
        else:
            self.node.get_logger().error(f"Unable to find function {function_name} to create action")
            return None

    def run_action(self, input_index: int, msg: Joy):
        """Invoke the validated function

        Args:
            input_index (int): index of the button/axis pushed
            msg (Joy): the joystick message that initiated the action
        """
        self.functor(input_index, msg)


def create_action(action_definition: dict, node: Node) -> RunnableAction:
    """Factory method to create an action from a YAML dictionary

    Args:
        action_definition (dict): YAML description of the action
        node (Node): supporting node

    Raises:
        RuntimeError: Raised if there is an error parsing the YAML description

    Returns:
        RunnableAction: an action that may be executed
    """

    constructors = {"service": ServiceAction, "function": FunctionAction}

    action_type_to_create = action_definition["action_type"]
    if action_type_to_create in constructors:
        return constructors[action_type_to_create](action_definition["action"], node)
    else:
        raise RuntimeError(f"Invalid action_type '{action_type_to_create}' in entry:\n\t{str(action_definition)}")


# Container class for actions
class ActionMap:

    def __init__(self, node: Node):
        """Constructor

        Args:
            node (Node): Owning node for the actions
        """
        super().__init__()
        self.actions = {}
        self.node = node

    def add_action(self, yaml_action: dict):
        """Add an action to the set

        Args:
            yaml_action (dict): YAML dictionary containing the action definition
        """
        required_fields = ("input_index", "input_type", "action_type", "action")
        try:
            for field in required_fields:
                if field not in yaml_action:
                    raise RuntimeError(f"Missing '{field}' in action definition")

            new_action = create_action(yaml_action, self.node)
            self._add_action(new_action, yaml_action["input_type"], int(yaml_action["input_index"]))
        except RuntimeError as e:
            self.node.get_logger().error(f"Error adding action: {str(e)} for entry:\n\t{str(yaml_action)}")

    def _add_action(self, action: RunnableAction, input_type: str, input_index: int):
        """Internal function to facilitate adding an action

        Args:
            action (RunnableAction): action to add
            input_type (str): button or axis
            input_index (int): which button or axis
        """
        if input_type not in self.actions:
            self.actions[input_type] = {}
        if input_index not in self.actions[input_type]:
            self.actions[input_type][input_index] = []
        self.actions[input_type][input_index].append(action)

    def run_action(self, msg: Joy, input_type: str, input_index: int):
        """Run any actions corresponding to the given input type and index

        Args:
            msg (Joy): joystick message driving the action
            input_type (str): button or axis
            input_index (int): which button or axis
        """
        if input_type in self.actions and input_index in self.actions[input_type]:
            for action in self.actions[input_type][input_index]:
                action.run_action(input_index, msg)


# Main node
class PhoebeJoystickSafing(Node):
    def __init__(self):
        super().__init__("phoebe_joystick_safing")

        # Subscribe to the joystick topic
        self.subscription = self.create_subscription(Joy, "/joy_teleop/joy", self.joy_callback, 10)

        # Grab parameter values
        self.declare_parameter("actions_file", "", ParameterDescriptor(description="Path to the actions file."))
        self.declare_parameter(
            "axis_tolerance",
            0.01,
            ParameterDescriptor(description='How much motion on an axis constitutes "movement."'),
        )
        self.axis_tolerance = self.get_parameter("axis_tolerance").value

        # Process the config file
        actions_file = self.get_parameter("actions_file").value
        self.get_logger().info(f"Joystick Safing node running from actions in {actions_file}")

        self.action_map = ActionMap(self)
        self.actions = self.read_actions_from_file(actions_file)
        self.previous_state: Joy = None  # Previous state of the joystick (used to detect changes)

    def read_actions_from_file(self, actions_file: str):
        """Read actions from a YAML file

        Args:
            actions_file (str): name of the file
        """

        # Read the actions file and parse the actions it contains into the action map
        try:
            with open(actions_file) as actions_file_stream:
                actions_content = yaml.safe_load(actions_file_stream)

                for thing in actions_content["actions"]:
                    self.get_logger().info("Read: " + str(thing))
                    self.action_map.add_action(thing)

        except FileNotFoundError:
            self.get_logger().fatal(f"Cannot open actions config file: {actions_file}")
        except yaml.YAMLError as e:
            self.get_logger().fatal(f"Unable to parse actions file {actions_file}: {e}")

    def print_value(self, axis_index: int, msg: Joy):
        """Test function for dumping current axis value to the screen

        Args:
            axis_index (int): which axis
            msg (Joy): the joystick message driving the action
        """
        self.get_logger().info(f"Value of axis {axis_index} is {msg.axes[axis_index]}")

    def joy_callback(self, msg: Joy):
        """Main callback for incoming joystick messages

        Args:
            msg (Joy): current joystick message
        """

        # For the first message, there is nothing to compare against, so store state and return
        if self.previous_state is None:
            self.previous_state = msg
            return

        # Sanity test
        assert len(msg.buttons) == len(self.previous_state.buttons)
        assert len(msg.axes) == len(self.previous_state.axes)

        buttons_activated = [
            index
            for index in range(0, len(msg.buttons))
            if self.previous_state.buttons[index] == 0 and msg.buttons[index] == 1
        ]
        # Loop through the activated buttons. If there are associated actions, run them
        for button_index in buttons_activated:
            self.action_map.run_action(msg, "button", button_index)

        # Check for axis changes
        axes_activated = [
            index
            for index in range(0, len(msg.axes))
            if math.fabs(msg.axes[index] - self.previous_state.axes[index]) > self.axis_tolerance
        ]
        # Loop through the activated axes. If there are associated actions, run them
        for axis_index in axes_activated:
            self.action_map.run_action(msg, "axis", axis_index)

        # Store off state for comparison with the next message
        self.previous_state = msg


def main(args=None):
    rclpy.init(args=args)
    joystick_safing_node = PhoebeJoystickSafing()
    try:
        rclpy.spin(joystick_safing_node)
    except KeyboardInterrupt:
        pass
    finally:
        joystick_safing_node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
