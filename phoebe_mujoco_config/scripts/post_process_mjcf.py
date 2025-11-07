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

    # copy the cylinder mockup and jig into the assets directory
    shutil.copy2(
        f'{get_package_share_directory("phoebe_mujoco_config")}/resources/cylinder_mockup_short_final_mm_1.stl',
        f"{filepath}/assets",
    )

    # copy the april tags into the assets directory
    shutil.copy2(
        f'{get_package_share_directory("phoebe_mujoco_config")}/resources/tag36_11_00001.png',
        f"{filepath}/assets",
    )
    shutil.copy2(
        f'{get_package_share_directory("phoebe_mujoco_config")}/resources/tag36_11_00004.png',
        f"{filepath}/assets",
    )

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

    # Replace the wheels with the custom wheels xml
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

    # change the class of the fingers from collision to rubber, and add rubber pads
    # Get all elements with the tag name geom
    geom_elements = dom.getElementsByTagName("geom")

    # Filter by attribute value containing a substring
    for elem in geom_elements:
        if "finger_v6_collision" in elem.getAttribute("mesh"):
            elem.setAttribute("class", "rubber")

    rubber_vis_element = dom.createElement("geom")
    rubber_col_element = dom.createElement("geom")
    rubber_elems = [rubber_vis_element, rubber_col_element]
    for rubber_elem in rubber_elems:
        rubber_elem.setAttribute("size", "0.001 0.012 0.01")
        rubber_elem.setAttribute("pos", "-0.002 0.00325 0.061")
        rubber_elem.setAttribute("quat", "1 0 0 0")
        rubber_elem.setAttribute("type", "box")
        rubber_elem.setAttribute("rgba", "0.1 0.1 0.1 1")
    rubber_vis_element.setAttribute("class", "visual")
    rubber_col_element.setAttribute("class", "rubber")

    for elem in body_elements:
        if "right_finger" in elem.getAttribute("name"):
            elem.appendChild(rubber_vis_element.cloneNode(True))
            elem.appendChild(rubber_col_element.cloneNode(True))

    print(f"writing to {filepath_full}")

    with open(filepath_full, "w") as file:
        # Remove extra newlines that minidom adds after each tag
        xml_data = "\n".join([line for line in dom.toprettyxml(indent="  ").splitlines() if line.strip()])
        file.write(xml_data)


if __name__ == "__main__":
    filepath = "mjcf_data"
    main(filepath)
