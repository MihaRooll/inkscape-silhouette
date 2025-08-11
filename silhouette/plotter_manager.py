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

from .Graphtec import DEVICE, SilhouetteCameo

class PlotterManager:
    """High level helper to discover and drive Silhouette plotters."""

    def __init__(self, log=None):
        self.log = log if log is not None else sys.stdout

    # ------------------------------------------------------------------
    def find_plotters(self) -> List[Dict[str, int]]:
        """Return a list of connected plotters understood by this package."""
        found: List[Dict[str, int]] = []
        if usb is None:
            # PyUSB not installed at all – nothing we can do here but inform the
            # caller so they at least know why discovery is empty.
            self.log.write("PyUSB not available, skipping device discovery\n")
            return found

        # ``usb.core.find`` may raise ``NoBackendError`` when the system lacks a
        # suitable libusb backend.  In that situation the caller should be told
        # explicitly rather than seeing an empty list without explanation.
        try:
            usb.find(find_all=True)
        except Exception:
            self.log.write("USB backend not available, no devices can be listed\n")
            return found

        for hardware in DEVICE:
            try:
                dev = usb.find(
                    idVendor=hardware["vendor_id"],
                    idProduct=hardware["product_id"],
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
        if platform.startswith("linux"):
            rules_dst = "/etc/udev/rules.d/99-silhouette.rules"
            if os.path.exists(rules_dst):
                self.log.write("udev rules already installed\n")
            else:
                rules_src = os.path.join(
                    os.path.dirname(__file__), "..", "silhouette-udev.rules"
                )
                subprocess.run(["sudo", "cp", rules_src, rules_dst], check=False)
                subprocess.run(
                    ["sudo", "udevadm", "control", "--reload-rules"], check=False
                )
                subprocess.run(["sudo", "udevadm", "trigger"], check=False)
                self.log.write("udev rules installed, please replug your device\n")
        elif platform.startswith("win"):
            zadig = os.path.join("distribute", "win", "zadig-2.4.exe")
            if os.path.exists(zadig):
                subprocess.Popen(["start", "", zadig], shell=True)
                self.log.write("Launched Zadig to install USB drivers\n")
            else:
                self.log.write("Zadig executable not found, cannot install drivers\n")
        else:
            self.log.write("Driver installation not supported on this platform\n")

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
