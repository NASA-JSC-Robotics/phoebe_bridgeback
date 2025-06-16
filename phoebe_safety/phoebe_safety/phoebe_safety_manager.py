#!/usr/bin/env python3
import rclpy
from rclpy.executors import MultiThreadedExecutor
from phoebe_safety.pb_safety_light_manager import PhoebeSafetyManager
from phoebe_safety.estop_manager import PhoebeEstopManager


def main(args=None):
    rclpy.init(args=args)
    estop_manager_node = PhoebeEstopManager()
    # simulate the arduino until we can run it on the actual hardware
    safety_manager_node = PhoebeSafetyManager(True)
    executor = MultiThreadedExecutor()
    executor.add_node(estop_manager_node)
    executor.add_node(safety_manager_node)
    try:
        executor.spin()
    finally:
        estop_manager_node.destroy_node()
        safety_manager_node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
