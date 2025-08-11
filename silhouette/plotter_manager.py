import os
import sys
import subprocess
from typing import List, Dict, Optional
import argparse

try:
    import usb.core  # type: ignore
except Exception:  # pragma: no cover
    usb = None
else:
    usb = usb.core

from .Graphtec import DEVICE, VENDOR_ID_GRAPHTEC, SilhouetteCameo

class PlotterManager:
    """High level helper to discover and drive Silhouette plotters."""

    def __init__(self, log=None):
        self.log = log if log is not None else sys.stdout

    # ------------------------------------------------------------------
    def find_plotters(self) -> List[Dict[str, int]]:
        """Return a list of connected plotters understood by this package."""
        found: List[Dict[str, int]] = []
        if usb is None:
            return found

        for hardware in DEVICE:
            try:
                dev = usb.find(
                    idVendor=hardware['vendor_id'],
                    idProduct=hardware['product_id'],
                )
            except Exception:
                dev = None
            if dev is not None:
                found.append(hardware)
        return found

    # ------------------------------------------------------------------
    def install_drivers(self) -> None:
        """Try to ensure the operating system has the required drivers."""
        platform = sys.platform.lower()
        if platform.startswith('linux'):
            rules_dst = '/etc/udev/rules.d/99-silhouette.rules'
            if not os.path.exists(rules_dst):
                rules_src = os.path.join(os.path.dirname(__file__), '..', 'silhouette-udev.rules')
                subprocess.run(['sudo', 'cp', rules_src, rules_dst], check=False)
                subprocess.run(['sudo', 'udevadm', 'control', '--reload-rules'], check=False)
                subprocess.run(['sudo', 'udevadm', 'trigger'], check=False)
        elif platform.startswith('win'):
            zadig = os.path.join('distribute', 'win', 'zadig-2.4.exe')
            if os.path.exists(zadig):
                subprocess.Popen(['start', '', zadig], shell=True)
        # macOS currently requires manual driver installation

    # ------------------------------------------------------------------
    def connect(self, dry_run: bool = False) -> SilhouetteCameo:
        """Connect to the first available plotter and return the driver object."""
        return SilhouetteCameo(log=self.log, dry_run=dry_run)

    # ------------------------------------------------------------------
    def send_svg_to_cut(self, svg_path: str, args: Optional[List[str]] = None) -> None:
        """Send an SVG file to the connected plotter for cutting."""
        from sendto_silhouette import SendtoSilhouette

        effect = SendtoSilhouette()
        cmd_args = args[:] if args else []
        cmd_args.append(svg_path)
        effect.run(cmd_args)


def cut_svg(svg_path: str, args: Optional[List[str]] = None) -> None:
    """Convenience wrapper to send an SVG file to the plotter for cutting."""
    PlotterManager().send_svg_to_cut(svg_path, args=args)


def main(argv: Optional[List[str]] = None) -> int:
    """Simple CLI for interacting with attached plotters."""
    parser = argparse.ArgumentParser(description="Manage Silhouette plotters")
    parser.add_argument("svg", nargs="?", help="SVG file to cut")
    parser.add_argument("--list", action="store_true", help="list connected plotters")
    parser.add_argument("--install-drivers", action="store_true", help="install required drivers")
    ns = parser.parse_args(argv)

    mgr = PlotterManager()
    if ns.list:
        devices = mgr.find_plotters()
        for dev in devices:
            print(f"Found plotter vendor={dev['vendor_id']:04x} product={dev['product_id']:04x}")
        if not devices:
            print("No plotters detected")
        return 0
    if ns.install_drivers:
        mgr.install_drivers()
        return 0
    if ns.svg:
        mgr.send_svg_to_cut(ns.svg)
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
