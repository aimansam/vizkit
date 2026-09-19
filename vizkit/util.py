"""Internal utilities."""
from __future__ import annotations
from pathlib import Path

from PIL import ImageFont

from .color import Theme, _theme_from_spec


def _pil_font(size: int):
    """Return a default PIL font at the given size."""
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _theme_from_spec(spec) -> Theme:
    """Accept a Theme instance, a string name, or None."""
    if isinstance(spec, Theme):
        return spec
    if isinstance(spec, str):
        if spec.lower() == "dark":
            return Theme.dark()
        return Theme.light()
    return Theme.light()
