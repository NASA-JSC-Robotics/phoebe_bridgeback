# Copyright (c) 2026, United States Government, as represented by the
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

import threading

import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.qos import (
    QoSProfile,
    QoSReliabilityPolicy,
    QoSDurabilityPolicy,
    QoSHistoryPolicy,
)

from sensor_msgs.msg import JointState


VOLATILE_QOS = QoSProfile(
    reliability=QoSReliabilityPolicy.RELIABLE,
    durability=QoSDurabilityPolicy.VOLATILE,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=1,
)


def _spin_executor(executor):
    try:
        executor.spin()
    except rclpy.executors.ExternalShutdownException:
        pass


class JointStateSubscriber:
    """
    Subscribes to joint states on its own executor thread.

    This helps avoid slowdowns in other node topics / timers / callbacks, as joint states
    will eat up the executor's loop rate.

    Args:
        node_name: Name for the internal ROS node.
        topic: Joint states topic to subscribe to.
        joint_names: If provided, only messages containing ALL of these
                     joint names will be stored. Messages from other publishers
                     that don't include these joints are discarded.
    """

    def __init__(
        self,
        node_name="joint_state_listener",
        topic="/joint_states",
        joint_names=None,
    ):
        self.last_joint_state = None
        self._required_joints = set(joint_names) if joint_names else None

        def joint_state_cb(msg):
            if self._required_joints is not None:
                msg_joints = set(msg.name)
                if not self._required_joints.issubset(msg_joints):
                    return
            self.last_joint_state = msg

        self._js_node = Node(node_name)
        self._js_sub = self._js_node.create_subscription(JointState, topic, joint_state_cb, VOLATILE_QOS)

        self._js_executor = SingleThreadedExecutor()
        self._js_executor.add_node(self._js_node)
        self._js_thread = threading.Thread(target=_spin_executor, daemon=True, args=(self._js_executor,))
        self._js_thread.start()

    def shutdown(self):
        self._js_node.destroy_node()
        self._js_executor.shutdown()
        self._js_thread.join()
        self._js_node = None
