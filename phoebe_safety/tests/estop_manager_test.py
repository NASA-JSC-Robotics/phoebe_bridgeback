#!/usr/bin/env python3
import rclpy
import threading
import unittest
import time

import rclpy
from phoebe_safety.estop_manager import PhoebeEstopManager
from phoebe_safety.estop_manager import RobotState
from mock_controller_manager import MockControllerManager
from rclpy.executors import MultiThreadedExecutor
import threading

class EstopManagerTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        rclpy.try_shutdown()

    def setUp(self):
        self.estop_node = PhoebeEstopManager()
        self.estop_executor = MultiThreadedExecutor()
        self.estop_executor.add_node(self.estop_node)
        self.estop_executor_thread = threading.Thread(target=self.estop_executor.spin, daemon=True)
        self.estop_executor_thread.start()

        self.mock_cm_node = MockControllerManager()
        self.mock_cm_executor = MultiThreadedExecutor()
        self.mock_cm_executor.add_node(self.mock_cm_node)
        self.mock_cm_executor_thread = threading.Thread(target=self.mock_cm_executor.spin, daemon=True)
        self.mock_cm_executor_thread.start()

    def tearDown(self):
        self.estop_node.destroy_node()
        self.estop_executor.shutdown()

        self.mock_cm_node.destroy_node()
        self.mock_cm_executor.shutdown()

    def test_estop_construction(self):
        assert self.estop_node.robot_state == RobotState.ESTOP

    def test_mock_cm_load(self):
        assert self.mock_cm_node.controllers is not None

if __name__ == "__main__":
    unittest.main(verbosity=2)