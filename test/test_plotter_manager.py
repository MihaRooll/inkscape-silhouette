from silhouette import PlotterManager


def test_find_plotters_returns_list():
    pm = PlotterManager()
    devices = pm.find_plotters()
    assert isinstance(devices, list)
