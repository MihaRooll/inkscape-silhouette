"""Silhouette helper package.

This package exposes a small helper API for managing Silhouette plotters.  The
actual implementation lives in :mod:`plotter_manager` but importing that module
on package import caused problems for ``python -m silhouette.plotter_manager``
because the module would already be in ``sys.modules`` before execution.  To
avoid that and still provide the convenience symbols at the package level we
perform a lazy import via ``__getattr__``.
"""

__all__ = ["PlotterManager", "cut_svg"]


def __getattr__(name):
    if name in __all__:
        from . import plotter_manager

        return getattr(plotter_manager, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")

