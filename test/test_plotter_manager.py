import subprocess
import sys

from silhouette import PlotterManager, cut_svg


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
