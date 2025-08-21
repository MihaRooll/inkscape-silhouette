#!/usr/bin/env python3
"""Demonstrate parallel dry-run jobs for two plotter selectors."""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
import threading
from typing import List

from silhouette.Graphtec import SilhouetteCameo

# Simple square path in millimeters
SQUARE = [[(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]]


def cut_job(selector: str) -> None:
    """Run a dummy cut job for ``selector``."""
    print(f"Starting job for {selector}")
    plotter = SilhouetteCameo(log=sys.stdout, dry_run=True)
    plotter.plot(mediawidth=20, mediaheight=20, pathlist=SQUARE)
    print(f"Finished job for {selector}")


def main(args: List[str]) -> None:
    selectors = args[:2] if args else ["selectorA", "selectorB"]
    threads = [threading.Thread(target=cut_job, args=(sel,)) for sel in selectors]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


if __name__ == "__main__":
    main(sys.argv[1:])
