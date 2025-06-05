#!/usr/bin/env python3
import rclpy
import threading
import unittest
import time

# from controller_manager_msgs.srv import ListControllers
from phoebe_safety import pb_safety_light_manager
from phoebe_interfaces.msg import SafetyStatus
from std_msgs.msg import Bool


class PhoebeSafetyLightManagerTest(unittest.TestCase):

    TIMEOUT = 2.0

    @classmethod
    def setUpClass(cls):
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        rclpy.try_shutdown()

    def setUp(self):
        self.node = pb_safety_light_manager.PhoebeSafetyManager(sim_arduino=True)
        self.status_msg = None

        self.executor = rclpy.executors.MultiThreadedExecutor()
        self.executor.add_node(self.node)

        self.executor_thread = threading.Thread(target=self.executor.spin, daemon=True)
        self.executor_thread.start()

    def tearDown(self):
        self.node.destroy_node()
        self.executor.shutdown()

    def status_cb(self, msg):
        """
        Callback for receiving status from the light manager node.
        """
        self.status_msg = msg

    def test_construction(self):
        # Just verify the defaults
        assert not self.node.estop_active
        assert self.node.controller_active

    def test_estop_callback(self):
        # Verify that published estop messages correctly update the state and publish appropriate messages.

        test_node = rclpy.create_node("test_publisher")
        e_stop_pub = test_node.create_publisher(Bool, self.node.estop_topic, 1)
        test_node.create_subscription(SafetyStatus, self.node.safety_status_topic, self.status_cb, 1)

        tmp_executor = rclpy.executors.MultiThreadedExecutor()
        tmp_executor.add_node(test_node)
        tmp_executor_thread = threading.Thread(target=tmp_executor.spin, daemon=True)
        tmp_executor_thread.start()

        # Publish an estop message
        msg = Bool()
        msg.data = True
        e_stop_pub.publish(msg)

        # Wait for confirmation or a timeout
        start = time.time()
        while not self.node.estop_active and not time.time() - start > self.TIMEOUT:
            time.sleep(0.1)

        # Verify the e-stop was set
        assert self.node.estop_active

        # Wait for the status message to be published
        start = time.time()
        while not self.status_msg and not time.time() - start > self.TIMEOUT:
            time.sleep(0.1)

        # Verify the correct status message
        assert self.status_msg.status == SafetyStatus.SAFE_TO_ENTER

    def test_controller_manager(self):

        assert not self.node.last_cm_stamp

        # Create and add a node to the ROS env
        test_node = rclpy.create_node("controller_manager")
        tmp_executor = rclpy.executors.MultiThreadedExecutor()
        tmp_executor.add_node(test_node)
        tmp_executor_thread = threading.Thread(target=tmp_executor.spin, daemon=True)
        tmp_executor_thread.start()

        # Verify the node is detected
        start = time.time()
        while not self.node.last_cm_stamp and not time.time() - start > self.TIMEOUT:
            time.sleep(0.1)

        # Verify the stamp was set
        assert self.node.last_cm_stamp

        # TODO: More?


if __name__ == "__main__":
    unittest.main(verbosity=2)
