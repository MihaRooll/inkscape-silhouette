import subprocess
import sys
from pathlib import Path

from silhouette import PlotterManager, cut_svg
import silhouette.plotter_manager as pm_module
import usb.core


def test_find_plotters_returns_list():
    pm = PlotterManager()
    devices = pm.find_plotters()
    assert isinstance(devices, list)


def test_cut_svg_callable():
    assert callable(cut_svg)


def test_cli_help_displays_usage():
    result = subprocess.run(
        [sys.executable, "-m", "silhouette.plotter_manager", "--help"],
        stdout=subprocess.PIPE,
        text=True,
    )
    assert "Manage Silhouette plotters" in result.stdout


def test_cli_list_no_devices(monkeypatch, capsys):
    monkeypatch.setattr(pm_module.PlotterManager, "find_plotters", lambda self: [])
    pm_module.main(["--list"])
    assert "No plotters detected" in capsys.readouterr().out


def test_find_plotters_handles_no_backend(monkeypatch, capsys):
    class DummyUSB:
        def find(self, *args, **kwargs):
            raise usb.core.NoBackendError("no backend")

    monkeypatch.setattr(pm_module, "usb", DummyUSB())
    pm = pm_module.PlotterManager()
    assert pm.find_plotters() == []
    assert "USB backend not available" in capsys.readouterr().out


def test_ensure_libusb_loads_dll(monkeypatch, tmp_path, capsys):
    dll = tmp_path / "libusb-1.0.dll"
    dll.write_bytes(b"")

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("PATH", "")

    from silhouette import usb_backend

    monkeypatch.setattr(usb_backend, "_find_libusb_dll", lambda: str(dll))

    import usb.backend.libusb1 as libusb1

    called = {}

    def fake_get_backend(*, find_library=None):
        called["dll"] = find_library("libusb-1.0.dll") if find_library else None
        class Dummy:
            pass
        return Dummy()

    monkeypatch.setattr(libusb1, "get_backend", fake_get_backend)

    from silhouette.usb_backend import ensure_libusb

    ensure_libusb(verbose=True)
    out = capsys.readouterr().out
    assert "libusb" in out
    assert called["dll"] == str(dll)


def test_find_libusb_dll_checks_bin(monkeypatch, tmp_path):
    pkg_dir = tmp_path / "libusb_package"
    (pkg_dir / "bin").mkdir(parents=True)
    dll = pkg_dir / "bin" / "libusb-1.0.dll"
    dll.write_bytes(b"")
    (pkg_dir / "__init__.py").write_text("")

    import sys

    monkeypatch.syspath_prepend(tmp_path)
    sys.modules.pop("libusb_package", None)

    from silhouette import usb_backend

    assert usb_backend._find_libusb_dll() == str(dll)


def test_cli_preprocess_creates_output(tmp_path, monkeypatch):
    svg = tmp_path / "in.svg"
    svg.write_text("<svg></svg>")

    fake_inkscape = tmp_path / "inkscape"
    fake_inkscape.write_text("#!/bin/sh\nexit 0")
    fake_inkscape.chmod(0o755)
    monkeypatch.setenv("INKSCAPE_PATH", str(fake_inkscape))

    def fake_run(cmd, check):
        for arg in cmd:
            if isinstance(arg, str) and arg.startswith("--export-plain-svg="):
                Path(arg.split("=", 1)[1]).write_text("<svg></svg>")

    monkeypatch.setattr(subprocess, "run", fake_run)

    called = {}

    def fake_send(self, path, args=None):
        called["path"] = path

    monkeypatch.setattr(pm_module.PlotterManager, "send_svg_to_cut", fake_send)

    pm_module.main(["--preprocess", str(svg)])

    assert called["path"].endswith("_out.svg")
    assert Path(called["path"]).exists()
