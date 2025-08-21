#!/usr/bin/env python3
"""List USB devices relevant to Silhouette plotters."""

import sys
try:
    import usb.core  # type: ignore
    import usb.util  # type: ignore
except Exception as exc:  # pragma: no cover
    sys.exit(f"PyUSB not available: {exc}")


def main() -> None:
    print("selector\tvid:pid\tmanufacturer product\tserial")
    for dev in usb.core.find(find_all=True):
        vid = getattr(dev, "idVendor", 0)
        pid = getattr(dev, "idProduct", 0)
        bus = getattr(dev, "bus", 0)
        addr = getattr(dev, "address", 0)
        try:
            serial = usb.util.get_string(dev, dev.iSerialNumber) if dev.iSerialNumber else ""
        except Exception:
            serial = ""
        try:
            mfr = usb.util.get_string(dev, dev.iManufacturer) if dev.iManufacturer else ""
        except Exception:
            mfr = ""
        try:
            prod = usb.util.get_string(dev, dev.iProduct) if dev.iProduct else ""
        except Exception:
            prod = ""
        selector = f"{vid:04x}:{pid:04x}:{bus}-{addr}"
        print(f"{selector}\t{vid:04x}:{pid:04x}\t{mfr} {prod}\t{serial}")


if __name__ == "__main__":
    main()
