#!/usr/bin/env python3
#
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

# this file is modified from this repository with several modifications and fixes
# https://github.com/JunHeonYoon/mujoco_mecanum/


import argparse
from math import (
    pi,
    sin,
    cos,
    sqrt,
)
import numpy as np
import os
import sys

n_roller = 8  # number of rollers of wheel
pos = [
    0,
    0,
    0,
]  # position of wheel wrt body frame
mass = 2.5  # mass of a wheel
diag_inertia = [
    0.00720101,
    0.00490071,
    0.00490071,
]  # diagonal inertia of a wheel [ixx, iyy, izz]
size = [
    0.0759,
    0.077 * sqrt(2) / 2,
]  # size of a wheel [radius, width] - width is roller length * sqrt(2)/2
roller_r = 0.033 / 2
counter = 1  # keep track for writing unique names to file


def return_wheel_description(
    link_name,
    pos,
    wheel_type,
):
    global counter
    wheel_description = ""

    x = pos[0]
    y = pos[1]
    z = pos[2]

    ixx = diag_inertia[0]
    iyy = diag_inertia[1]
    izz = diag_inertia[2]

    r = size[0]
    h = size[1]

    cylinder = f"""<body name="{link_name}_link" pos="{str(x)} {str(y)} {str(z)}">
    <inertial pos="0 0 0" quat="0.707107 0 0 0.707107" mass="{str(mass)}" diaginertia="{str(ixx)} {str(iyy)} {str(izz)}" />
    <joint name="{link_name}_joint" pos="0 0 0" axis="0 1 0" damping="5.0"/>
    """
    # <geom size="{str(r)} {str(h/2)}" quat="0.707107 0.707107 0 0" type="cylinder" rgba="0.2 0.2 0.2 0.5" class="visual"/>
    wheel_description += cylinder + "\n"

    step = (2 * pi) / n_roller

    for i in range(n_roller):
        body_name = link_name + "_roller_" + str(i)
        joint_name = link_name + "_slipping_" + str(i)

        pin_1 = np.array(
            [
                (r - roller_r) * cos(step * i),
                -h / 2,
                (r - roller_r) * sin(step * i),
            ]
        )

        if wheel_type == 0:
            if i == n_roller - 1:
                pin_2 = np.array(
                    [
                        (r - roller_r) * cos(step * 0),
                        h / 2,
                        (r - roller_r) * sin(step * 0),
                    ]
                )
            else:
                pin_2 = np.array(
                    [
                        (r - roller_r) * cos(step * (i + 1)),
                        h / 2,
                        (r - roller_r) * sin(step * (i + 1)),
                    ]
                )
        else:
            if i == 0:
                pin_2 = np.array(
                    [
                        (r - roller_r) * cos(step * (n_roller - 1)),
                        h / 2,
                        (r - roller_r) * sin(step * (n_roller - 1)),
                    ]
                )
            else:
                pin_2 = np.array(
                    [
                        (r - roller_r) * cos(step * (i - 1)),
                        h / 2,
                        (r - roller_r) * sin(step * (i - 1)),
                    ]
                )

        axis = pin_2 - pin_1
        pos = pin_1 + axis / 2

        wheel = f"""
    <geom size="{str(roller_r)}" fromto="{str(pin_1[0])} {str(pin_1[1])} {str(pin_1[2])} {str(pin_2[0])} {str(pin_2[1])} {str(pin_2[2])}" quat="1 0 0 0" type="capsule" rgba="0.2 0.2 0.2 1" class="visual"/>
    <body name="{body_name}_link" pos="{str(pos[0])} {str(pos[1])} {str(pos[2])}" zaxis="{str(axis[0])} {str(axis[1])} {str(axis[2])}">
        <joint name="{joint_name}_joint" type="hinge" pos="0 0 0" axis="0 0 1" damping="0.1" limited="false" actuatorfrclimited="false"/>
        <inertial pos="0 0 0" quat="0.711549 0.711549 0 0 " mass="0.001" diaginertia="0.00001 0.00001 0.00001" />
        <geom name="mecanum_wheel{counter}" mesh="mecanum_wheel_22" quat="1 0 0 0" rgba="0.2 0.2 0.2 1" class="wheels"/>
    </body>"""

        counter = counter + 1

        wheel_description += wheel + "\n"

    wheel_description += "</body>" + "\n"
    return wheel_description


def main():
    parser = argparse.ArgumentParser(
        description="Generate wheels for PB mujoco sim",
    )
    parser.add_argument("--tf-prefix", default="", help="tf_prefix for generated wheels")

    # Skip ros args
    args_without_filename = sys.argv[1:]
    while "--ros-args" in args_without_filename:
        args_without_filename.remove("--ros-args")
    parsed_args = parser.parse_args(args_without_filename)

    tf_prefix = parsed_args.tf_prefix

    total_description = "<mujoco>\n"
    total_description += return_wheel_description(
        link_name=f"{tf_prefix}rear_left_wheel",
        pos=[
            -0.319,
            0.2755,
            0.05,
        ],
        wheel_type=0,
    )
    total_description += return_wheel_description(
        link_name=f"{tf_prefix}rear_right_wheel",
        pos=[
            -0.319,
            -0.2755,
            0.05,
        ],
        wheel_type=1,
    )
    total_description += return_wheel_description(
        link_name=f"{tf_prefix}front_left_wheel",
        pos=[
            0.319,
            0.2755,
            0.05,
        ],
        wheel_type=1,
    )
    total_description += return_wheel_description(
        link_name=f"{tf_prefix}front_right_wheel",
        pos=[
            0.319,
            -0.2755,
            0.05,
        ],
        wheel_type=0,
    )
    total_description += "</mujoco>\n"

    file_path = "mjcf_data/wheels.xml"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)  # make directory if missing

    open(
        file_path,
        "w",
    ).write(total_description)


if __name__ == "__main__":

    main()
