#!/usr/bin/python3
import rclpy
import sys
from phoebe_status_handler_py.status_ncurses_frontend import StatusNcursesFrontend
from phoebe_status_handler_py.status_display_node import StatusDisplayNode


def main(args=None):
    rclpy.init(args=args)
    display = StatusNcursesFrontend()
    # Specify None to write state to the terminal. Useful if the display is broken.
    # display = None
    status_node = StatusDisplayNode(display)
    rclpy.spin(status_node)

    status_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main(sys.argv)
