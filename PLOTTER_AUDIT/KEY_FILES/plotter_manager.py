# Source: silhouette/plotter_manager.py
import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import argparse

try:
    import usb.core  # type: ignore
    import usb.util  # type: ignore
except Exception:  # pragma: no cover
    usb = None
else:
    usb = usb.core
    usb_util = usb.util

from .usb_backend import ensure_libusb

ensure_libusb()

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
            self.log.write("PyUSB not available, skipping device discovery\n")
            return found

        try:
            devices = list(usb.find(find_all=True))
        except Exception:
            self.log.write("USB backend not available, no devices can be listed\n")
            return found

        for dev in devices:
            vid = int(getattr(dev, "idVendor", 0))
            pid = int(getattr(dev, "idProduct", 0))
            mfr = prod = ""
            try:
                if dev.iManufacturer:
                    mfr = usb_util.get_string(dev, dev.iManufacturer) or ""
                if dev.iProduct:
                    prod = usb_util.get_string(dev, dev.iProduct) or ""
            except Exception:
                pass

            is_candidate = vid == 0x0B4D or any(
                s in (mfr + prod) for s in ("Silhouette", "Graphtec")
            )
            if not is_candidate:
                continue

            info: Dict[str, int] = {"vendor_id": vid, "product_id": pid}
            for hw in DEVICE:
                if hw["vendor_id"] == vid and hw["product_id"] == pid:
                    info.update(hw)
                    break
            else:
                info["name"] = "unknown PID"
            found.append(info)
        return found

    # ------------------------------------------------------------------
    def dump_usb_devices(self) -> None:
        """Print all USB devices for debugging purposes."""
        if usb is None:
            self.log.write("PyUSB not available, skipping device dump\n")
            return
        try:
            devices = list(usb.find(find_all=True))
        except Exception:
            self.log.write("USB backend not available, no devices can be listed\n")
            return
        for dev in devices:
            vid = getattr(dev, "idVendor", 0)
            pid = getattr(dev, "idProduct", 0)
            try:
                mfr = usb_util.get_string(dev, dev.iManufacturer) if dev.iManufacturer else ""
            except Exception:
                mfr = ""
            try:
                prod = usb_util.get_string(dev, dev.iProduct) if dev.iProduct else ""
            except Exception:
                prod = ""
            self.log.write(f"{vid:04x}:{pid:04x} {mfr} {prod}\n")

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


def _find_inkscape() -> Optional[str]:
    """Best-effort attempt at locating the Inkscape binary."""

    env = os.environ.get("INKSCAPE_PATH")
    if env and os.path.exists(env):
        return env
    if sys.platform.startswith("win"):
        default = r"C:\Program Files\Inkscape\bin\inkscape.com"
        if os.path.exists(default):
            return default
    for name in ("inkscape", "inkscape.com"):
        path = shutil.which(name)  # type: ignore
        if path:
            return path
    return None


def _preprocess_svg(svg_path: str) -> str:
    """Convert text in ``svg_path`` to paths using Inkscape and return new path."""

    inkscape = _find_inkscape()
    if not inkscape:
        raise FileNotFoundError("Inkscape executable not found")
    base = str(Path(svg_path).with_suffix(""))
    out_path = base + "_out.svg"
    actions = "select-all:all;object-to-path;stroke-to-path;export-do;file-close-all"
    cmd = [
        inkscape,
        svg_path,
        f"--export-plain-svg={out_path}",
        f"--actions={actions}",
    ]
    subprocess.run(cmd, check=True)
    return out_path


def main(argv: Optional[List[str]] = None) -> int:
    """Simple CLI for interacting with attached plotters."""
    import shutil

    parser = argparse.ArgumentParser(description="Manage Silhouette plotters")
    parser.add_argument("svg", nargs="?", help="SVG file to cut")
    parser.add_argument("--list", action="store_true", help="list connected plotters")
    parser.add_argument("--install-drivers", action="store_true", help="install required drivers")
    parser.add_argument("--dump-usb", action="store_true", help="dump all USB devices")
    parser.add_argument("--preprocess", action="store_true", help="preprocess SVG with Inkscape")
    parser.add_argument("--speed", type=int, help="cut speed")
    parser.add_argument("--pressure", type=int, help="cut pressure")
    parser.add_argument("--tool", help="tool type")
    parser.add_argument("--mat", dest="mat", help="cutting mat")
    parser.add_argument("--passes", type=int, dest="passes", help="number of passes")
    parser.add_argument("--smoothness", type=float, help="path smoothness")
    parser.add_argument("--verbose", action="store_true", help="verbose output")
    ns = parser.parse_args(argv)

    ensure_libusb(verbose=ns.verbose)
    mgr = PlotterManager()
    if ns.dump_usb:
        mgr.dump_usb_devices()
        return 0
    if ns.list:
        devices = mgr.find_plotters()
        for dev in devices:
            name = dev.get("name", "")
            extra = f" ({name})" if name else ""
            print(f"Found plotter vendor={dev['vendor_id']:04x} product={dev['product_id']:04x}{extra}")
        if not devices:
            print("No plotters detected")
        return 0
    if ns.install_drivers:
        mgr.install_drivers()
        return 0
    if ns.svg:
        svg = ns.svg
        if ns.preprocess:
            svg = _preprocess_svg(svg)
        args: List[str] = []
        for opt in ("speed", "pressure", "tool", "mat", "passes", "smoothness"):
            val = getattr(ns, opt)
            if val is not None:
                args.extend([f"--{opt}", str(val)])
        mgr.send_svg_to_cut(svg, args=args)
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
