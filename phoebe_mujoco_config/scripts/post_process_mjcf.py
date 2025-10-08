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

from xml.dom import minidom
import shutil
from ament_index_python.packages import get_package_share_directory


def main(filepath):
    filepath_full = filepath + "/mujoco_description_formatted.xml"
    # Load your XML document
    dom = minidom.parse(filepath_full)

    # add the mesh mecanum_wheel_22.stl to the assets
    asset_elements = dom.getElementsByTagName("asset")
    asset_element = asset_elements[0]

    mecanum_wheel_element = dom.createElement("mesh")
    mecanum_wheel_element.setAttribute("file", "mecanum_wheel_22.stl")
    mecanum_wheel_element.setAttribute("scale", "0.001 0.001 0.001")
    asset_element.appendChild(mecanum_wheel_element)

    # copy the mecanum wheel 22 mesh into the assets directory
    shutil.copy2(
        f'{get_package_share_directory("phoebe_mujoco_config")}/resources/mecanum_wheel_22.stl',
        f"{filepath}/assets",
    )

    # Get all elements with the tag name body
    body_elements = dom.getElementsByTagName("body")

    include_element = dom.createElement("include")
    include_element.setAttribute("file", "wheels.xml")

    # Filter by attribute value containing a substring
    first_time = True
    for elem in body_elements:
        if "wheel_link" in elem.getAttribute("name"):
            if first_time:
                elem.parentNode.replaceChild(include_element, elem)
                first_time = False
            else:
                elem.parentNode.removeChild(elem)

    print(f"writing to {filepath_full}")

    with open(filepath_full, "w") as file:
        # Remove extra newlines that minidom adds after each tag
        xml_data = "\n".join([line for line in dom.toprettyxml(indent="  ").splitlines() if line.strip()])
        file.write(xml_data)


if __name__ == "__main__":
    filepath = "mjcf_data"
    main(filepath)
