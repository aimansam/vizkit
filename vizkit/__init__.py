"""vizkit -- Beautiful data visualization from CSV/JSON in 3 lines of code.

Bar, line, scatter, heatmap, and pie charts with sensible defaults,
color themes, and export to PNG. Built on Pillow (no heavy dependencies).
"""

__version__ = "1.0.0"
__all__ = ["Chart", "Theme", "Data"]

from .chart import Chart, Theme, save_chart, save_png
from .data import Data
