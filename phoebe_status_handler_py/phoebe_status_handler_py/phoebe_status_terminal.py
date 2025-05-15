#!/usr/bin/python3
import rclpy
import sys
import argparse
from phoebe_status_handler_py.status_ncurses_frontend import StatusNcursesFrontend
from phoebe_status_handler_py.status_display_node import StatusDisplayNode
import rclpy.parameter


def main(args=None):
    rclpy.init(args=args)

    display = StatusNcursesFrontend()
    # Specify None to write state to the terminal. Useful if the display is broken
    # or as a sanity check
    #display = None
    
    status_node = StatusDisplayNode(display)
    rclpy.spin(status_node)

    status_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main(sys.argv)
