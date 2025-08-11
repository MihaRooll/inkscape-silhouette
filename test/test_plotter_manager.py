import subprocess
import sys

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


def test_find_plotters_handles_no_backend(monkeypatch, capsys):
    class DummyUSB:
        def find(self, *args, **kwargs):
            raise usb.core.NoBackendError("no backend")

    monkeypatch.setattr(pm_module, "usb", DummyUSB())
    pm = pm_module.PlotterManager()
    assert pm.find_plotters() == []
    assert "USB backend not available" in capsys.readouterr().out
