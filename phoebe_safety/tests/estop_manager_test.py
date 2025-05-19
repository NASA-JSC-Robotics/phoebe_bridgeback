import pytest
import rclpy
from phoebe_safety.estop_manager import PhoebeEstopManager
from mock_controller_manager import MockControllerManager
from rclpy.executors import MultiThreadedExecutor
import threading


class TestMyNode:
    @classmethod
    def setup(cls):
        cls.running = True

        rclpy.init()
        cls.phoebe_node = PhoebeEstopManager()
        cls.mock_cm_node = MockControllerManager()
        cls.phoebe_executor = MultiThreadedExecutor()
        cls.mock_cm_executor = MultiThreadedExecutor()
        cls.phoebe_executor.add_node(cls.phoebe_node)
        cls.mock_cm_executor.add_node(cls.mock_cm_node)

        def spin_phoebe():
            while cls.running:
                cls.phoebe_executor.spin_once()
        def spin_mock_cm():
            while cls.running:
                cls.mock_cm_executor.spin_once()

        cls.phoebe_thread = threading.Thread(target=spin_phoebe)
        cls.mock_cm_thread = threading.Thread(target=spin_mock_cm)

    @classmethod
    def teardown(cls):
        cls.phoebe_thread.join()
        cls.mock_cm_thread.join()

        cls.node.destroy_node()
        rclpy.shutdown()


    def test_my_method(self):
        # Your test logic here
        self.setup()
        assert True # Example assertion
        self.teardown()