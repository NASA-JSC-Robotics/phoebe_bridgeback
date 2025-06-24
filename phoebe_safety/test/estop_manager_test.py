#!/usr/bin/env python3
import rclpy
import threading
import unittest
from std_msgs.msg import Bool
from std_srvs.srv import Trigger
from phoebe_safety.estop_manager import PhoebeEstopManager
from phoebe_safety.estop_manager import RobotState
from mock_controller_manager import MockControllerManager
from rclpy.executors import MultiThreadedExecutor
import time
from controller_manager_msgs.srv import SwitchController


class EstopManagerTest(unittest.TestCase):

    TIMEOUT = 3.0

    @classmethod
    def setUpClass(cls):
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        rclpy.try_shutdown()

    def setUp(self):
        self.estop_node = PhoebeEstopManager()

        self.mock_cm_node = MockControllerManager()

        self.estop_pub_node = rclpy.create_node("estop_publisher")
        self.estop_state = True
        self.estop_pub = self.estop_pub_node.create_publisher(Bool, self.estop_node.estop_topic_name, 1)
        self.estop_pub_timer = self.estop_pub_node.create_timer(1.0, self.pub_estop_cb)

        self.executor = MultiThreadedExecutor()
        self.executor.add_node(self.estop_node)
        self.executor.add_node(self.mock_cm_node)
        self.executor.add_node(self.estop_pub_node)
        self.executor_thread = threading.Thread(target=self.executor.spin)
        self.executor_thread.start()

    def tearDown(self):
        self.testDone = False

        self.estop_node.destroy_node()
        self.mock_cm_node.destroy_node()
        self.estop_pub_node.destroy_node()

        self.executor.shutdown()

    def pub_estop_cb(self):
        # Publish the estop message - True is estopped, false is not estopped
        msg = Bool()
        msg.data = self.estop_state
        self.estop_pub.publish(msg)

    def set_estop_state(self, estop_state):
        self.estop_state = estop_state

    def request_service(self, service_name):
        test_node = rclpy.create_node(f"{service_name}_caller")
        service_client = test_node.create_client(Trigger, f"phoebe_estop_manager/{service_name}")

        service_client_executor = MultiThreadedExecutor()
        service_client_executor.add_node(test_node)
        service_client_executor_thread = threading.Thread(target=service_client_executor.spin, daemon=True)
        service_client_executor_thread.start()

        # Publish the estop message - True is estopped, false is not estopped
        srv = Trigger.Request()
        response = service_client.call(srv)

        test_node.destroy_node()
        service_client_executor.shutdown()
        return response.success

    def set_controller_states(self, activate_controllers=[], deactivate_controllers=[]):
        test_node = rclpy.create_node("switch_controller_caller")
        service_client = test_node.create_client(SwitchController, "controller_manager/switch_controller")

        service_client_executor = MultiThreadedExecutor()
        service_client_executor.add_node(test_node)
        service_client_executor_thread = threading.Thread(target=service_client_executor.spin, daemon=True)
        service_client_executor_thread.start()

        srv = SwitchController.Request()
        srv.activate_controllers = activate_controllers
        srv.deactivate_controllers = deactivate_controllers

        response = service_client.call(srv)

        test_node.destroy_node()
        service_client_executor.shutdown()
        return response.ok

    def start_robot(self):
        self.set_estop_state(False)

    def start_and_then_estop(self):
        self.start_robot()

        self.wait_for_robot_state(RobotState.RUNNING, self.TIMEOUT)

        self.set_estop_state(True)
        self.wait_for_robot_state(RobotState.ESTOP, self.TIMEOUT)

        # wait for controllers to be disabled
        start = time.time()
        while (self.mock_cm_node.any_controllers_with_command_interfaces_active()) and (
            time.time() - start
        ) < self.TIMEOUT:
            time.sleep(0.1)

        # return true if we have successfully disabled controllers
        return not self.mock_cm_node.any_controllers_with_command_interfaces_active()

    def wait_for_robot_state(self, state, timeout):
        start = time.time()
        while (not self.estop_node.robot_state == state) and (time.time() - start) < timeout:
            time.sleep(0.1)

        return self.estop_node.robot_state == state

    def test_estop_construction(self):
        self.estop_node.get_logger().info("starting test_estop_construction")
        assert self.estop_node.robot_state == RobotState.ESTOP

    def test_mock_cm_load(self):
        self.estop_node.get_logger().info("starting test_mock_cm_load")
        assert self.mock_cm_node.controllers is not None

    def test_set_to_running(self):
        self.estop_node.get_logger().info("starting test_set_to_running")
        # should be in initially estopped state
        assert self.estop_node.robot_state == RobotState.ESTOP

        # set estop state to false to test entering the program
        self.start_robot()

        self.wait_for_robot_state(RobotState.RUNNING, self.TIMEOUT)
        assert (
            self.estop_node.robot_state == RobotState.RUNNING
        ), "Did not switch to running state after estop released at beginning"

    def test_cancel_controllers_on_estop(self):
        self.estop_node.get_logger().info("starting test_cancel_controllers_on_estop")
        self.start_robot()

        self.wait_for_robot_state(RobotState.RUNNING, self.TIMEOUT)
        assert self.estop_node.robot_state == RobotState.RUNNING

        # make sure that some controllers are active at the beginning
        assert self.mock_cm_node.any_controllers_with_command_interfaces_active()

        self.set_estop_state(True)
        self.wait_for_robot_state(RobotState.ESTOP, self.TIMEOUT)

        # wait for controllers to be disabled
        start = time.time()
        while (self.mock_cm_node.any_controllers_with_command_interfaces_active()) and (
            time.time() - start
        ) < self.TIMEOUT:
            time.sleep(0.1)

        # make sure that required controllers are turned off
        assert not self.mock_cm_node.any_controllers_with_command_interfaces_active()

    def test_controller_turned_off_after_incorrect_controller_enable(self):
        self.estop_node.get_logger().info("starting test_controller_turned_off_after_incorrect_controller_enable")
        self.start_and_then_estop()

        # try to turn on a controller
        assert self.set_controller_states(activate_controllers=["platform_velocity_controller"])

        # wait for controllers to be disabled
        start = time.time()
        while (self.mock_cm_node.any_controllers_with_command_interfaces_active()) and (
            time.time() - start
        ) < self.TIMEOUT:
            time.sleep(0.1)

        # make sure that required controllers are turned off
        assert not self.mock_cm_node.any_controllers_with_command_interfaces_active()

    def test_controller_stay_off_after_only_estop_disable(self):
        self.estop_node.get_logger().info("starting test_controller_stay_off_after_only_estop_disable")
        self.start_and_then_estop()

        # turn off the estop, and make sure that we don't go back to a running state or turn on controllers
        self.set_estop_state(False)

        # wait a bit to make sure that we don't get something coming up after some time
        time.sleep(self.TIMEOUT)

        # make sure that required controllers are turned off
        assert not self.mock_cm_node.any_controllers_with_command_interfaces_active()

        # make sure that we are still in estop mode
        assert self.estop_node.robot_state == RobotState.ESTOP

    def test_controller_stay_off_after_only_safe_reset(self):
        self.estop_node.get_logger().info("starting test_controller_stay_off_after_only_safe_reset")
        self.start_and_then_estop()

        # turn off the estop, and make sure that we don't go back to a running state or turn on controllers
        self.request_service("request_restart")

        # wait a bit to make sure that we don't get something coming up after some time
        time.sleep(self.TIMEOUT)

        # make sure that required controllers are turned off
        assert not self.mock_cm_node.any_controllers_with_command_interfaces_active()

        # make sure that we are still in estop mode
        assert self.estop_node.robot_state == RobotState.ESTOP

    def test_controllers_reset_after_cleared(self):
        self.estop_node.get_logger().info("starting test_controllers_reset_after_cleared")
        self.start_robot()

        self.wait_for_robot_state(RobotState.RUNNING, self.TIMEOUT)

        active_controllers = self.mock_cm_node.get_active_controllers()

        self.set_estop_state(True)
        self.wait_for_robot_state(RobotState.ESTOP, self.TIMEOUT)

        # wait for controllers to be disabled
        start = time.time()
        while (self.mock_cm_node.any_controllers_with_command_interfaces_active()) and (
            time.time() - start
        ) < self.TIMEOUT:
            time.sleep(0.1)

        # make sure we have successfully disabled controllers
        assert not self.mock_cm_node.any_controllers_with_command_interfaces_active()

        # turn off the estop, and request the restart
        self.set_estop_state(False)
        assert self.request_service("request_restart")

        # wait for controllers to be re-enabled
        start = time.time()
        while (active_controllers != self.mock_cm_node.get_active_controllers()) and (time.time() - start) < 5.0:
            time.sleep(0.1)

        # make sure that required controllers are turned off
        assert active_controllers == self.mock_cm_node.get_active_controllers()


if __name__ == "__main__":
    unittest.main(verbosity=2)
