#!/usr/bin/python3
import rclpy
import sys
<<<<<<< HEAD
import argparse
from phoebe_status_handler_py.status_ncurses_frontend import StatusNcursesFrontend
from phoebe_status_handler_py.status_display_node import StatusDisplayNode
import rclpy.parameter
=======
from phoebe_status_handler_py.status_ncurses_frontend import StatusNcursesFrontend
from phoebe_status_handler_py.status_display_node import StatusDisplayNode
>>>>>>> 90bbd3004ff42b8db9ab94481526a16864005470


def main(args=None):
    rclpy.init(args=args)
<<<<<<< HEAD

    display = StatusNcursesFrontend()
    # Specify None to write state to the terminal. Useful if the display is broken
    # or as a sanity check
    #display = None
    
=======
    display = StatusNcursesFrontend()
    # Specify None to write state to the terminal. Useful if the display is broken.
    # display = None
>>>>>>> 90bbd3004ff42b8db9ab94481526a16864005470
    status_node = StatusDisplayNode(display)
    rclpy.spin(status_node)

    status_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main(sys.argv)
