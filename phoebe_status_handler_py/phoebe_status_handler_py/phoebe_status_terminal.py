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
