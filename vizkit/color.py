"""Color utilities: named colors, themes, gradients."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Sequence


@dataclass
class Color:
    """An sRGB color as (r, g, b) 0-255 ints."""

    r: int = 0
    g: int = 0
    b: int = 0

    @classmethod
    def from_hex(cls, hex_str: str) -> "Color":
        h = hex_str.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return cls(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    def to_hex(self, alpha: int | None = None) -> str:
        s = f"#{self.r:02x}{self.g:02x}{self.b:02x}"
        if alpha is not None:
            s += f"{alpha:02x}"
        return s

    def __repr__(self) -> str:
        return f"Color({self.r}, {self.g}, {self.b})"


def _theme_from_spec(spec) -> "Theme":
    """Accept a Theme instance, a string name, or None."""
    if isinstance(spec, Theme):
        return spec
    if isinstance(spec, str):
        if spec.lower() == "dark":
            return Theme.dark()
        return Theme.light()
    return Theme.light()


# Named palette — vibrant, colorblind-friendly
PALETTE = {
    "cerulean": Color.from_hex("#007BA7"),
    "sunflower": Color.from_hex("#FFC300"),
    "crimson": Color.from_hex("#D62828"),
    "emerald": Color.from_hex("#06A77D"),
    "violet": Color.from_hex("#7B2CBF"),
    "sandy": Color.from_hex("#E9C46A"),
    "slate": Color.from_hex("#457B9D"),
    "charcoal": Color.from_hex("#264653"),
    "coral": Color.from_hex("#EF476F"),
    "sky": Color.from_hex("#118AB2"),
    "orange": Color.from_hex("#FB8500"),
    "teal": Color.from_hex("#1A936F"),
}


def sequential_gradient(start: Color, end: Color, n: int) -> list[Color]:
    """Interpolate n colors from start to end."""
    if n <= 1:
        return [start]
    out: list[Color] = []
    for i in range(n):
        t = i / (n - 1)
        out.append(Color(
            int(start.r + (end.r - start.r) * t),
            int(start.g + (end.g - start.g) * t),
            int(start.b + (end.b - start.b) * t),
        ))
    return out


@dataclass
class Theme:
    """A color theme + style preset for charts."""

    name: str = "default"
    primary: Color = field(default_factory=lambda: PALETTE["cerulean"])
    secondary: Color = field(default_factory=lambda: PALETTE["sunflower"])
    accent: Color = field(default_factory=lambda: PALETTE["crimson"])
    background: Color = field(default_factory=lambda: Color(255, 255, 255))
    text: Color = field(default_factory=lambda: Color(38, 70, 83))
    grid: Color = field(default_factory=lambda: Color(220, 220, 220))
    sequence: list[Color] = field(default_factory=lambda: [
        PALETTE["cerulean"], PALETTE["sunflower"], PALETTE["crimson"],
        PALETTE["emerald"], PALETTE["violet"], PALETTE["sandy"],
        PALETTE["slate"], PALETTE["coral"], PALETTE["sky"], PALETTE["orange"],
    ])

    @classmethod
    def dark(cls) -> "Theme":
        t = cls(name="dark")
        t.background = Color(38, 46, 53)
        t.text = Color(255, 255, 255)
        t.grid = Color(70, 80, 90)
        t.primary = PALETTE["sky"]
        t.secondary = PALETTE["sunflower"]
        t.accent = PALETTE["coral"]
        t.sequence = [
            PALETTE["sky"], PALETTE["sunflower"], PALETTE["coral"],
            PALETTE["teal"], PALETTE["violet"], PALETTE["sandy"],
        ]
        return t

    @classmethod
    def light(cls) -> "Theme":
        return cls(name="light")

    def color_for(self, index: int) -> Color:
        return self.sequence[index % len(self.sequence)]
