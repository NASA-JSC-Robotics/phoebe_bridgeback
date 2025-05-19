#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Header, Bool
from std_srvs.srv import Trigger
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup, MutuallyExclusiveCallbackGroup
from controller_manager_msgs.srv import ListControllers, SwitchController
from rclpy.qos import QoSProfile, ReliabilityPolicy
from enum import Enum


class RobotState(Enum):
    RUNNING = 0
    ESTOP = 1
    FREEDRIVE = 2


class MessageMonitor:
    def __init__(self, name, node, initial_state, valid_time_seconds, timeout_state):
        self.name = name
        self.node = node
        self.status = initial_state
        self.msg_data = False
        self.last_msg_time = None

        self.valid_time = valid_time_seconds
        self.timeout_state = timeout_state

    def set_status(self, status):
        self.status = status
        self.last_msg_time = self.node.get_clock().now()

    def get_status(self):
        if self.name == "restart":
            print(self.status)
        # if we haven't gotten a mssage yet, return the initial state
        if self.last_msg_time is None:
            return self.status

        # if we have timed out, return the timeout state
        current_time = self.node.get_clock().now()
        if (current_time - self.last_msg_time) > rclpy.duration.Duration(seconds=self.valid_time):
            self.node.get_logger().info(f"timeout for {self.name}")
            return self.timeout_state
        # otherwise, return the actual state
        else:
            return self.status


class PhoebeEstopManager(Node):
    def __init__(self):
        super().__init__("phoebe_estop_manager")

        self.robot_state = RobotState.RUNNING

        # Use ROS 2 parameter system
        self.freedrive_controller_name = (
            self.declare_parameter("freedrive_controller_name", "freedrive_mode_controller")
            .get_parameter_value()
            .string_value
        )

        # Callback group for multithreading
        self.main_cbg = ReentrantCallbackGroup()
        self.manager_cbg = MutuallyExclusiveCallbackGroup()
        self.freedrive_cbg = MutuallyExclusiveCallbackGroup()
        self.restart_cbg = MutuallyExclusiveCallbackGroup()

        self.rate_hz = 5

        self.stopped_controllers = []

        self.is_estopped = False
        self.estop_message_monitor = MessageMonitor(
            name="estop",
            node=self,
            initial_state=False,
            valid_time_seconds=2,
            timeout_state=True,
        )

        self.is_freedrive_mode_requested = False
        self.freedrive_message_monitor = MessageMonitor(
            name="freedrive",
            node=self,
            initial_state=False,
            valid_time_seconds=2,
            timeout_state=False,
        )

        self.is_restart_requested = False
        self.restart_message_monitor = MessageMonitor(
            name="restart",
            node=self,
            initial_state=False,
            valid_time_seconds=2,
            timeout_state=False,
        )

        # Subscribing to estop topic
        qos_profile = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT, depth=10)
        self.subscription = self.create_subscription(
            Bool, "ridgeback/platform/emergency_stop", self.estop_callback, qos_profile, callback_group=self.manager_cbg
        )
        # Publishing to "safety_status" topic with the custom SafetyStatus message
        self.hb_publisher = self.create_publisher(Header, "~/heartbeat", 10, callback_group=self.main_cbg)

        # Timer to check system s￼tatus at 5 Hz (every 0.2 seconds)
        self.rate_hz = 5
        self.timer = self.create_timer(1 / self.rate_hz, self.manager_loop, callback_group=self.main_cbg)

        # Create client for controller manager service
        self.list_controllers_client = self.create_client(
            ListControllers, "controller_manager/list_controllers", callback_group=self.main_cbg
        )
        # wait until all required services are available from controller_manager
        self.get_logger().info("Waiting for list controllers service to come up on controller_manager/list_controllers")
        self.list_controllers_client.wait_for_service()
        self.get_logger().info("Service available")

        # Create client for controller manager service
        self.switch_controllers_client = self.create_client(
            SwitchController, "controller_manager/switch_controller", callback_group=self.main_cbg
        )
        # wait until all required services are available from controller_manager
        self.get_logger().info(
            "Waiting for switch controller service to come up on controller_manager/switch_controller"
        )
        self.switch_controllers_client.wait_for_service()
        self.get_logger().info("Service available")

        self.request_freedrive_mode_server = self.create_service(
            Trigger, "~/request_freedrive_mode", self.request_freedrive_mode
        )
        self.request_restart_server = self.create_service(Trigger, "~/request_restart", self.request_restart)

        # Logger
        self.get_logger().info(f"This node has started: {self.get_name()}")

    def estop_callback(self, msg: Bool):
        """
        Callback for the /emergency_stop topic.
        True = active. False = not active.
        Updates state of emergency stop signal.
        """

        self.estop_message_monitor.set_status(msg.data)

    def request_freedrive_mode(self, request, response):
        self.freedrive_message_monitor.set_status(True)

        timeout_seconds = 2.0
        timeout = rclpy.duration.Duration(seconds=timeout_seconds)

        start_time = self.get_clock().now()
        while (self.get_clock().now() - start_time) < timeout:
            if self.robot_state == RobotState.FREEDRIVE:
                response.success = True
                return response

        # return failure if we didn't change to freedrive mode within the timeout
        response.success = False
        response.message = f"Did not switch into freedrive mode within {timeout_seconds} seconds"
        return response

    def request_restart(self, request, response):
        self.restart_message_monitor.set_status(True)
        print(self.restart_message_monitor.get_status())

        timeout_seconds = 2.0
        timeout = rclpy.duration.Duration(seconds=timeout_seconds)

        start_time = self.get_clock().now()
        while (self.get_clock().now() - start_time) < timeout:
            if self.robot_state == RobotState.RUNNING:
                response.success = True
                return response

        # return failure if we didn't change to running mode within the timeout
        response.success = False
        response.message = f"Did not switch into running mode within {timeout_seconds} seconds"
        return response

    def manager_loop(self):
        """
        Timer callback that evaluates system safety status.
        Publishes current safety status and updates light indicators.
        """

        is_estopped = self.estop_message_monitor.get_status()
        is_freedrive_mode_requested = self.freedrive_message_monitor.get_status()
        is_restart_requested = self.restart_message_monitor.get_status()

        self.get_logger().info(f"Robot State: {self.robot_state}")

        if self.robot_state == RobotState.RUNNING:
            # if we are estopped, set the state to estop
            if is_estopped:
                self.robot_state = RobotState.ESTOP
            elif is_freedrive_mode_requested:
                self.robot_state = RobotState.FREEDRIVE
                # reset the status back to false,
                self.freedrive_message_monitor.set_status(False)

            # if we are estopped or freedrive, disable can and stop controllers
            if self.robot_state in (RobotState.ESTOP, RobotState.FREEDRIVE):
                self.disable_can()
                self.stop_controllers(save_stopped_controllers=True)

        else:
            if is_estopped:
                self.robot_state = RobotState.ESTOP
            # if restart is requested, restart controllers and enable can
            elif is_restart_requested:
                self.restart_controllers()
                self.enable_can()
                self.robot_state = RobotState.RUNNING
                # reset the status back to false,
                self.restart_message_monitor.set_status(False)
            # otherwise, make sure that can is still disabled and controllers are stopped
            else:
                self.disable_can()
                self.stop_controllers(save_stopped_controllers=False)

        self.publish_hb_msg()

    def publish_hb_msg(self):
        hb_msg = Header()
        hb_msg.stamp = self.get_clock().now().to_msg()
        self.hb_publisher.publish(hb_msg)

    def enable_can(self):
        pass

    def disable_can(self):
        pass

    def stop_controllers(self, save_stopped_controllers):
        """Deactivates all of the controllers that are not listed as consistent.
        This can be called several times without causing issues. This is useful because
        some controllers may be turned back on in some cases, like if a trajectory is accidentally
        performed while the robot is disabled
        """

        # request to get switch controllers, list controllers
        switch_controller_request = SwitchController.Request()
        list_controllers_request = ListControllers.Request()

        # set strictness to strict to show that this fails if anything went wrong
        switch_controller_request.strictness = SwitchController.Request.STRICT
        switch_controller_request.timeout.nanosec = int(1.0e9)  # 0.5s

        # list the controllers that are running
        list_controllers_response = self.list_controllers_client.call(list_controllers_request)

        # each new time this is called, we will repopulate which controllers we are stopping
        controllers_to_stop = []

        # add controllers that are active and not consistent to the list to stop
        for controller in list_controllers_response.controller:
            if controller.state == "active" and len(controller.required_command_interfaces) > 0:
                if self.freedrive_controller_name not in controller.name:
                    controllers_to_stop.append(controller.name)

        # if there are any to stop, call switch_controllers to stop them
        if controllers_to_stop:
            switch_controller_request.deactivate_controllers = controllers_to_stop
            switch_controllers_response = self.switch_controllers_client.call(switch_controller_request)
            if not switch_controllers_response.ok:
                self.get_logger().error("Could not deactivate requested controllers")
            else:
                self.controllers_active = False

        # save the stopped controllers only if we are in a state where the controllers were active
        if save_stopped_controllers:
            self.stopped_controllers = controllers_to_stop

    def restart_controllers(self):
        """Reactivates all of the controllers that have been stopped by this node."""
        # initialize service requests
        switch_controller_request = SwitchController.Request()

        # set strictness to strict to show that this fails if anything went wrong
        switch_controller_request.strictness = SwitchController.Request.STRICT
        switch_controller_request.timeout.nanosec = int(0.5e9)  # 0.5s

        # turn off freedrive controllers if they are started
        list_controllers_request = ListControllers.Request()
        list_controllers_response = self.list_controllers_client.call(list_controllers_request)

        # add controllers that are active and not consistent to the list to stop
        stop_freedrive_controllers = []
        for controller in list_controllers_response.controller:
            if self.freedrive_controller_name in controller.name and controller.state == "active":
                stop_freedrive_controllers.append(controller.name)

        # only run this if we have logged that some controllers have been stopped
        if self.stopped_controllers or stop_freedrive_controllers:
            switch_controller_request.activate_controllers = self.stopped_controllers
            switch_controller_request.deactivate_controllers = stop_freedrive_controllers

            switch_controllers_response = self.switch_controllers_client.call(switch_controller_request)
            if not switch_controllers_response.ok:
                self.get_logger().error("Could not activate requested controllers")
            else:
                self.controllers_active = True

        # clear stopped controllers for the next round to populate
        self.stopped_controllers = []


def main(args=None):
    rclpy.init(args=args)
    node = PhoebeEstopManager()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
