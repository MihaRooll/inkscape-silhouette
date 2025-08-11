"""Silhouette helper package."""

# __init__ is needed for import statements across subdirectories.

from .plotter_manager import PlotterManager, cut_svg

__all__ = ["PlotterManager", "cut_svg"]

