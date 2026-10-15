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

"""
Rasterize a nav2 occupancy grid map straight from imetro_mobile_environment's
collision environment.

To run:

    python3 scripts/generate_environment_map.py -o /tmp/phoebe_xacro
    # writes /tmp/phoebe_xacro.pgm and /tmp/phoebe_xacro.yaml
"""

import argparse
import PyKDL
import trimesh
import xacro

from ament_index_python.packages import get_package_share_directory
import numpy as np
from pathlib import Path
from PIL import Image
from urdf_parser_py.urdf import URDF, Box, Mesh

DEFAULT_XACRO = (
    Path(get_package_share_directory("phoebe_description"))
    / "urdf"
    / "imetro_mobile_environment"
    / "imetro_mobile_environment.urdf.xacro"
)
ROOT_LINK = "world"


def kdl_frame(origin):
    if origin is None:
        return PyKDL.Frame()
    return PyKDL.Frame(PyKDL.Rotation.RPY(*origin.rpy), PyKDL.Vector(*origin.xyz))


def frame_to_rt(frame):
    rot = np.array([[frame.M[i, j] for j in range(3)] for i in range(3)])
    trans = np.array([frame.p.x(), frame.p.y(), frame.p.z()])
    return rot, trans


def resolve_mesh_path(filename):
    pkg, _, rel = filename.removeprefix("package://").partition("/")
    return Path(get_package_share_directory(pkg)) / rel


def convex_hull(points_xy):
    pts = sorted(set(map(tuple, points_xy)))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def box_corners(size):
    sx, sy, sz = (s / 2.0 for s in size)
    return np.array([[x, y, z] for x in (-sx, sx) for y in (-sy, sy) for z in (-sz, sz)])


def collect_collision_polygons(xacro_path):
    """Returns a list of world-frame 2D polygons (each an Nx2 array of xy points)."""

    robot = URDF.from_xml_string(xacro.process_file(str(xacro_path)).toxml())
    joint_by_child = {j.child: j for j in robot.joints}

    world_frame = {ROOT_LINK: PyKDL.Frame()}

    def fk(link_name):
        if link_name not in world_frame:
            joint = joint_by_child[link_name]
            world_frame[link_name] = fk(joint.parent) * kdl_frame(joint.origin)
        return world_frame[link_name]

    polygons = []
    for link in robot.links:
        link_frame = fk(link.name)
        for collision in link.collisions:
            shape_frame = link_frame * kdl_frame(collision.origin)
            rot, trans = frame_to_rt(shape_frame)
            geom = collision.geometry
            if isinstance(geom, Box):
                local_pts = box_corners(geom.size)
            elif isinstance(geom, Mesh):
                local_pts = trimesh.load_mesh(resolve_mesh_path(geom.filename)).vertices
            else:
                continue
            world_pts = (rot @ local_pts.T + trans[:, None]).T
            polygons.append(np.array(convex_hull(world_pts[:, :2])))
    return polygons


def rasterize(polygons, resolution, margin):
    from PIL import ImageDraw

    all_pts = np.vstack(polygons)
    min_x, min_y = all_pts.min(axis=0) - margin
    max_x, max_y = all_pts.max(axis=0) + margin
    width = int(np.ceil((max_x - min_x) / resolution))
    height = int(np.ceil((max_y - min_y) / resolution))

    # image row 0 = world y_max (map_server's origin is the bottom-left row).
    def to_pixel(pt):
        return ((pt[0] - min_x) / resolution, height - (pt[1] - min_y) / resolution)

    img = Image.new("L", (width, height), color=254)  # 254 = free
    draw = ImageDraw.Draw(img)
    for poly in polygons:
        draw.polygon([to_pixel(pt) for pt in poly], fill=0)  # 0 = occupied
    return img, (min_x, min_y)


def write_map(img, origin_xy, resolution, out_path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pgm_path = out_path.with_suffix(".pgm")
    img.save(pgm_path)

    yaml_path = out_path.with_suffix(".yaml")
    yaml_path.write_text(
        f"image: {pgm_path.name}\n"
        f"mode: trinary\n"
        f"resolution: {resolution}\n"
        f"origin: [{origin_xy[0]:.3f}, {origin_xy[1]:.3f}, 0]\n"
        f"negate: 0\n"
        f"occupied_thresh: 0.65\n"
        f"free_thresh: 0.196\n"
    )
    return pgm_path, yaml_path


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--xacro", type=Path, default=DEFAULT_XACRO, help="imetro_mobile_environment wrapper xacro")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path(get_package_share_directory("phoebe_description")) / "maps" / "phoebe",
        help="output path (without extension)",
    )
    parser.add_argument("--resolution", type=float, default=0.05, help="meters/pixel")
    parser.add_argument("--margin", type=float, default=1.0, help="meters of free space padded around the geometry")
    args = parser.parse_args()

    polygons = collect_collision_polygons(args.xacro)
    img, origin_xy = rasterize(polygons, args.resolution, args.margin)
    pgm_path, yaml_path = write_map(img, origin_xy, args.resolution, args.output)
    print(f"wrote {pgm_path} and {yaml_path} ({img.width}x{img.height} px)")


if __name__ == "__main__":
    main()
