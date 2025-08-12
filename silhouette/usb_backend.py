"""Utilities to ensure PyUSB has a working backend on Windows.

The :func:`ensure_libusb` helper loads a ``libusb-1.0.dll`` from either the
``libusb_package`` wheel or from the repository's ``distribute/win`` directory
and patches PyUSB so missing kernel driver helpers are treated as no-ops.  On
non-Windows platforms the function simply returns.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional


def _find_libusb_dll() -> Optional[str]:
    """Return a filesystem path to ``libusb-1.0.dll`` if it can be located."""

    # Try the optional ``libusb_package`` wheel which ships the DLL as data.
    try:  # pragma: no cover - only executed when package is available
        import importlib.resources as resources
        import libusb_package  # type: ignore

        base = resources.files(libusb_package)
        for rel in ("libusb-1.0.dll", os.path.join("bin", "libusb-1.0.dll")):
            try:
                with resources.as_file(base / rel) as dll:
                    if dll.exists():
                        return str(dll)
            except Exception:
                continue
    except Exception:
        pass

    # Fall back to a DLL shipped with the repository (mainly used in tests).
    candidate = Path(__file__).resolve().parent.parent / "distribute" / "win" / "libusb-1.0.dll"
    if candidate.exists():
        return str(candidate)
    return None


def _patch_backend() -> None:
    """Patch PyUSB's libusb1 backend so kernel-driver helpers are no-ops."""

    try:  # pragma: no cover - exercised indirectly
        import usb.backend.libusb1 as be

        be.is_kernel_driver_active = lambda *a, **k: False
        be.detach_kernel_driver = lambda *a, **k: None
        be.attach_kernel_driver = lambda *a, **k: None
    except Exception:
        pass


def ensure_libusb(verbose: bool = True) -> None:
    """Ensure a working libusb backend is available for PyUSB on Windows."""

    if not sys.platform.startswith("win"):  # pragma: no cover - only for Windows
        return

    dll = _find_libusb_dll()
    if dll:
        directory = os.path.dirname(dll)
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(directory)
        else:  # pragma: no cover - Python <3.8 on Windows
            os.environ["PATH"] = directory + os.pathsep + os.environ.get("PATH", "")
        if verbose:
            print(f"libusb: {dll}")
    elif verbose:
        print("libusb-1.0.dll not found")

    _patch_backend()

    if dll:
        try:  # pragma: no cover - exercised indirectly
            import usb.backend.libusb1 as be

            # Preload backend with explicit path to avoid NoBackendError
            be.get_backend(find_library=lambda _name: dll)
        except Exception:
            pass

