#!/usr/bin/env python3
"""Convert a simple SVG polyline to Graphtec commands (dry-run)."""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
import xml.etree.ElementTree as ET
from typing import List, Tuple

from silhouette.Graphtec import SilhouetteCameo


def _parse_svg_polylines(svg_path: str) -> List[List[Tuple[float, float]]]:
    ns = {"svg": "http://www.w3.org/2000/svg"}
    tree = ET.parse(svg_path)
    root = tree.getroot()
    polylines: List[List[Tuple[float, float]]] = []
    for elem in root.findall(".//svg:polyline", ns):
        points = elem.attrib.get("points", "").strip()
        pts: List[Tuple[float, float]] = []
        for part in points.split():
            if "," in part:
                x, y = part.split(",", 1)
                pts.append((float(x), float(y)))
        if pts:
            polylines.append(pts)
    return polylines


def main(svg_path: str | None = None) -> None:
    if svg_path:
        polylines = _parse_svg_polylines(svg_path)
    else:
        polylines = [[(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]]
    plotter = SilhouetteCameo(log=sys.stdout, dry_run=True)
    bbox = {"clip": {"urx": 100, "ury": 0, "llx": 0, "lly": 100}}
    cmds = plotter.plot_cmds(polylines, bbox, 0, 0)
    for cmd in cmds[:20]:
        print(cmd)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
