#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

from tf2_ros import TransformListener, Buffer
from geometry_msgs.msg import TransformStamped
from rclpy.duration import Duration
import numpy as np
from math import atan2, sqrt
import string

class PhoebeCalibrationNode(Node):
    def __init__(self):
        super().__init__('phoebe_calibration')

        self.declare_parameter('robot_side', 'right')
        self.robot_side: string = self.get_parameter('robot_side').get_parameter_value().string_value

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        timer_period = 1.0  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def tf_stamped_to_np(self, tf_stamped: TransformStamped):
        result = np.zeros((4, 4), dtype=float)

        # translation
        result[0,3] = tf_stamped.transform.translation.x
        result[1,3] = tf_stamped.transform.translation.y
        result[2,3] = tf_stamped.transform.translation.z
        result[3,3] = 1

        # orientation
        w = tf_stamped.transform.rotation.w
        x = tf_stamped.transform.rotation.x
        y = tf_stamped.transform.rotation.y
        z = tf_stamped.transform.rotation.z
        result[0,0] = 1 - 2*y*y - 2*z*z
        result[0,1] = 2*x*y - 2*w*z
        result[0,2] = 2*x*z + 2*w*y
        result[1,0] = 2*x*y + 2*w*z
        result[1,1] = 1 - 2*x*x - 2*z*z
        result[1,2] = 2*y*z - 2*w*x
        result[2,0] = 2*x*z - 2*w*y
        result[2,1] = 2*y*z + 2*w*x
        result[2,2] = 1 - 2*x*x - 2*y*y

        return result

    def print_transform(self, np_tf: np.ndarray, name: string):
        tf_string: string = "\n\t[{0:8.5f}, {1:8.5f}, {2:8.5f}, {3:8.5f}]".format(np_tf[0,0], np_tf[0,1], np_tf[0,2], np_tf[0,3]) +\
                            "\n\t[{0:8.5f}, {1:8.5f}, {2:8.5f}, {3:8.5f}]".format(np_tf[1,0], np_tf[1,1], np_tf[1,2], np_tf[1,3]) +\
                            "\n\t[{0:8.5f}, {1:8.5f}, {2:8.5f}, {3:8.5f}]".format(np_tf[2,0], np_tf[2,1], np_tf[2,2], np_tf[2,3]) +\
                            "\n\t[{0:8.5f}, {1:8.5f}, {2:8.5f}, {3:8.5f}]".format(np_tf[3,0], np_tf[3,1], np_tf[3,2], np_tf[3,3])

        self.get_logger().info(f"\n\n{name}: {tf_string}\n")

        roll=atan2(np_tf[2,1],np_tf[2,2])
        pitch=atan2(-np_tf[2,0],sqrt(np_tf[2,1]*np_tf[2,1]+np_tf[2,2]*np_tf[2,2]))
        yaw=atan2(np_tf[1,0],np_tf[0,0])

        urdf_string: string = "\n\nxyz=\"{0:.5f} {1:.5f} {2:.5f}\" ".format(np_tf[0,3], np_tf[1,3], np_tf[2,3]) + \
                              "rpy=\"{0:.5f} {1:.5f} {2:.5f}\"".format(roll, pitch, yaw)

        self.get_logger().info(urdf_string)

    def get_transform(self, source_frame, target_frame):
        try:
            now = rclpy.time.Time()
            trans: TransformStamped = self.tf_buffer.lookup_transform(
                source_frame,
                target_frame,
                now,
                timeout=Duration(seconds=1.0)
            )

            return self.tf_stamped_to_np(trans)
        except Exception as e:
            self.get_logger().warn(f"Could not transform {source_frame} to {target_frame}: {e}")

    def timer_callback(self):
        base = "default_mount"
        target = "calibration_face_target_side"
        cal_bot = self.robot_side + "_arm_mount_plate"
        cal_top = self.robot_side + "_arm_cal_link"
        ee = self.robot_side + "_calibration_face_robot_side"
        tf_base_cal_bot = self.get_transform(base, cal_bot)
        tf_cal_top_ee = self.get_transform(cal_top, ee)
        tf_base_target = self.get_transform(base, target)

        result = np.matmul(np.matmul(np.linalg.inv(tf_base_cal_bot),tf_base_target),np.linalg.inv(tf_cal_top_ee))
        self.print_transform(result, "result")

        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = PhoebeCalibrationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
