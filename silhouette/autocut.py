import tempfile
from pathlib import Path
from typing import List

from .plotter_manager import PlotterManager, _preprocess_svg
from .usb_backend import ensure_libusb

MAX_WIDTH_MM = 290
MAX_HEIGHT_MM = 500


def _build_svg(name: str, number: str) -> str:
    w = MAX_WIDTH_MM
    h = MAX_HEIGHT_MM
    name_y = h * 0.25
    number_y = h * 0.75
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}mm' height='{h}mm' viewBox='0 0 {w} {h}'>"
        f"<text x='{w/2}' y='{name_y}' font-family='Arial' font-size='{h*0.12}' "
        f"text-anchor='middle' lengthAdjust='spacingAndGlyphs' textLength='{w}'>{name}</text>"
        f"<text x='{w/2}' y='{number_y}' font-family='Arial' font-size='{h*0.45}' "
        f"text-anchor='middle' lengthAdjust='spacingAndGlyphs' textLength='{w}'>{number}</text>"
        "</svg>"
    )


def main(argv: List[str] | None = None) -> int:
    ensure_libusb(verbose=True)
    mgr = PlotterManager()
    devices = mgr.find_plotters()
    if not devices:
        print("No plotters detected, attempting driver installation...")
        mgr.install_drivers()
        devices = mgr.find_plotters()
        if not devices:
            print("No plotters available, aborting")
            return 1

    name = input("Введите ФИО: ")
    number = input("Введите номер: ")

    svg_content = _build_svg(name, number)
    with tempfile.TemporaryDirectory() as tmp:
        svg_path = Path(tmp, "layout.svg")
        svg_path.write_text(svg_content, encoding="utf-8")
        try:
            processed = _preprocess_svg(str(svg_path))
        except FileNotFoundError:
            print("Inkscape not found, sending raw SVG")
            processed = str(svg_path)
        mgr.send_svg_to_cut(processed, args=["--speed", "10", "--pressure", "3"])
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
