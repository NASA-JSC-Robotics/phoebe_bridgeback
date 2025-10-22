#!/usr/bin/env python3
#
# Copyright (c) 2025, United States Government, as represented by the
# Administrator of the National Aeronautics and Space Administration.
#
# All rights reserved.
#
# This software is licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import rclpy
from rclpy.executors import MultiThreadedExecutor
from phoebe_safety.pb_safety_light_manager import PhoebeSafetyManager
from phoebe_safety.estop_manager import PhoebeEstopManager


def main(args=None):
    rclpy.init(args=args)
    estop_manager_node = PhoebeEstopManager()
    # simulate the arduino until we can run it on the actual hardware
    safety_manager_node = PhoebeSafetyManager(False)
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
