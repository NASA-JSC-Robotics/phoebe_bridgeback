#!/usr/bin/python3
import rclpy
import sys
import argparse
from phoebe_status_handler_py.status_ncurses_frontend import StatusNcursesFrontend
from phoebe_status_handler_py.status_display_node import StatusDisplayNode
import rclpy.parameter


def main(args=None):
    rclpy.init(args=args)

    parser = argparse.ArgumentParser(
        epilog="Note that if specifying program args and ros args, program args must come first"
    )
    parser.add_argument(
        "-n", "--no-display", action="store_true", help="Print status to terminal but do not start an Ncurses display"
    )
    parsed_args, unknown_args = parser.parse_known_args()

    if parsed_args.no_display:
        display = None
    else:
        display = StatusNcursesFrontend()

    status_node = StatusDisplayNode(display)
    rclpy.spin(status_node)

    status_node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main(sys.argv)
