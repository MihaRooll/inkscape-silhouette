import builtins
import os

import silhouette.autocut as autocut


def test_build_svg_dimensions():
    svg = autocut._build_svg("Name", "12")
    assert "width='290mm'" in svg
    assert "height='500mm'" in svg


def test_main_invokes_cut(monkeypatch):
    inputs = iter(["Foo", "99"])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))

    called = {}

    class DummyPM:
        def find_plotters(self):
            return [{"vendor_id": 1, "product_id": 2}]

        def install_drivers(self):
            called["install"] = True

        def send_svg_to_cut(self, path, args=None):
            called["path"] = path
            called["exists"] = os.path.exists(path)

    monkeypatch.setattr(autocut, "PlotterManager", DummyPM)
    monkeypatch.setattr(autocut, "_preprocess_svg", lambda p: p)

    autocut.main([])
    assert called.get("exists")
