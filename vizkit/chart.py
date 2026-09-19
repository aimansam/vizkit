"""Chart engine: bar, line, scatter, heatmap, pie — rendered to SVG/PNG via Pillow."""

from __future__ import annotations
import math
import textwrap
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from .color import Color, PALETTE, Theme, sequential_gradient
from .data import Data
from .util import _pil_font, _theme_from_spec


# ── Geometry helpers ──────────────────────────────────────────────────

def _text_size(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    try:
        return draw.textbbox((0, 0), text, font=font)[2:4]
    except Exception:
        return draw.textsize(text, font=font)


def _wrap_text(text: str, max_width: int, font) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        if _text_size(None, trial, font)[0] <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [text]


# ── Bar chart ─────────────────────────────────────────────────────────

def _draw_bar(draw, x, y, w, h, color: Color, theme: Theme, width: int = 1) -> None:
    draw.rectangle([x, y, x + w, y + h], fill=color.to_hex(), outline=None)


def _render_bar(
    data: Data, x_col: str, y_col: str, theme: Theme,
    width: int = 800, height: int = 450, title: str = "",
    y_label: str = "", x_rotation: int = 0,
) -> Image.Image:
    vals_x = data.column(x_col)
    vals_y = data.column(y_col)
    n = len(vals_x)
    if n == 0:
        return _empty_image(width, height, theme, "No data")

    plot_w = width - 80
    plot_h = height - 100
    pad_l, pad_r, pad_t, pad_b = 60, 20, 50, 50

    y_min = min(vals_y)
    y_max = max(vals_y)
    if y_min == y_max:
        y_min -= 1
        y_max += 1
    y_range = y_max - y_min or 1

    bar_w = plot_w / n * 0.7
    gap = plot_w / n * 0.3
    font = _pil_font(11)
    title_font = _pil_font(14)

    img = Image.new("RGB", (width, height), theme.background.to_hex())
    d = ImageDraw.Draw(img)

    # Title
    if title:
        tw, th = _text_size(d, title, title_font)
        d.text(((width - tw) / 2, 12), title, fill=theme.text.to_hex(), font=title_font)

    # Y axis labels
    num_ticks = 5
    for i in range(num_ticks + 1):
        val = y_max - (y_max - y_min) * i / num_ticks
        y_pos = pad_t + plot_h - (plot_h * i / num_ticks)
        lbl = f"{val:,.0f}" if val == int(val) else f"{val:.1f}"
        tw, _ = _text_size(d, lbl, font)
        d.text((pad_l - tw - 6, y_pos - 6), lbl, fill=theme.text.to_hex(), font=font)
        d.line([pad_l, y_pos, pad_l + plot_w, y_pos], fill=theme.grid.to_hex(), width=1)

    # Bars
    for i in range(n):
        bar_h = (vals_y[i] - y_min) / y_range * plot_h
        x = pad_l + i * (bar_w + gap) + gap / 2
        color = theme.color_for(i)
        _draw_bar(d, int(x), int(pad_t + plot_h - bar_h), int(bar_w), int(bar_h), color, theme)

        # X label
        lbl = str(vals_x[i])
        if x_rotation:
            # rotated vertical label
            pass
        else:
            tw, th = _text_size(d, lbl, font)
            d.text((x + bar_w / 2 - tw / 2, pad_t + plot_h + 4), lbl, fill=theme.text.to_hex(), font=font)

    # Axes
    d.line([pad_l, pad_t, pad_l, pad_t + plot_h], fill=theme.text.to_hex(), width=2)
    d.line([pad_l, pad_t + plot_h, pad_l + plot_w, pad_t + plot_h], fill=theme.text.to_hex(), width=2)

    if y_label:
        ty = pad_t + plot_h / 2
        tx = 14
        d.text((tx, ty - 6), y_label, fill=theme.text.to_hex(), font=font)

    return img


# ── Line chart ────────────────────────────────────────────────────────

def _render_line(
    data: Data, x_col: str, y_col: str, theme: Theme,
    width: int = 800, height: int = 450, title: str = "",
    y_label: str = "", line_label: str = "",
) -> Image.Image:
    pts = data.pairs(x_col, y_col)
    n = len(pts)
    if n == 0:
        return _empty_image(width, height, theme, "No data")

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    if x_min == x_max:
        x_min -= 1; x_max += 1
    if y_min == y_max:
        y_min -= 1; y_max += 1
    x_range = x_max - x_min or 1
    y_range = y_max - y_min or 1

    plot_w = width - 80
    plot_h = height - 100
    pad_l, pad_r, pad_t, pad_b = 60, 20, 50, 50

    font = _pil_font(11)
    title_font = _pil_font(14)

    img = Image.new("RGB", (width, height), theme.background.to_hex())
    d = ImageDraw.Draw(img)

    if title:
        tw, th = _text_size(d, title, title_font)
        d.text(((width - tw) / 2, 12), title, fill=theme.text.to_hex(), font=title_font)

    num_ticks = 5
    for i in range(num_ticks + 1):
        val = y_max - (y_max - y_min) * i / num_ticks
        y_pos = pad_t + plot_h - (plot_h * i / num_ticks)
        lbl = f"{val:,.0f}" if val == int(val) else f"{val:.1f}"
        tw, _ = _text_size(d, lbl, font)
        d.text((pad_l - tw - 6, y_pos - 6), lbl, fill=theme.text.to_hex(), font=font)
        d.line([pad_l, y_pos, pad_l + plot_w, y_pos], fill=theme.grid.to_hex(), width=1)

    for i in range(n):
        x = pad_l + (xs[i] - x_min) / x_range * plot_w
        y = pad_t + plot_h - (ys[i] - y_min) / y_range * plot_h
        if i == 0:
            path = [(x, y)]
        else:
            path.append((x, y))
            d.line(path[-2:], fill=theme.primary.to_hex(), width=2)

    d.line(path, fill=theme.primary.to_hex(), width=2)

    # Points
    r = 4
    for x, y in path:
        d.ellipse([x - r, y - r, x + r, y + r], fill=theme.primary.to_hex(), outline=theme.background.to_hex())

    # X axis labels (first, mid, last)
    idxs = [0, n // 2, n - 1]
    for i in idxs:
        if i >= n:
            continue
        x_pos = pad_l + (xs[i] - x_min) / x_range * plot_w
        lbl = f"{xs[i]:,.0f}" if xs[i] == int(xs[i]) else f"{xs[i]:.1f}"
        tw, _ = _text_size(d, lbl, font)
        d.text((x_pos - tw / 2, pad_t + plot_h + 4), lbl, fill=theme.text.to_hex(), font=font)

    d.line([pad_l, pad_t, pad_l, pad_t + plot_h], fill=theme.text.to_hex(), width=2)
    d.line([pad_l, pad_t + plot_h, pad_l + plot_w, pad_t + plot_h], fill=theme.text.to_hex(), width=2)

    if y_label:
        d.text((14, pad_t + plot_h / 2 - 6), y_label, fill=theme.text.to_hex(), font=font)

    if line_label:
        lx = pad_l + plot_w - 10
        ly = pad_t + 15
        d.ellipse([lx - 4, ly - 4, lx + 4, ly + 4], fill=theme.primary.to_hex())
        tw, _ = _text_size(d, line_label, font)
        d.text((lx + 8, ly - 6), line_label, fill=theme.text.to_hex(), font=font)

    return img


# ── Scatter chart ─────────────────────────────────────────────────────

def _render_scatter(
    data: Data, x_col: str, y_col: str, theme: Theme,
    width: int = 800, height: int = 450, title: str = "",
    y_label: str = "",
) -> Image.Image:
    pts = data.pairs(x_col, y_col)
    n = len(pts)
    if n == 0:
        return _empty_image(width, height, theme, "No data")

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    if x_min == x_max:
        x_min -= 1; x_max += 1
    if y_min == y_max:
        y_min -= 1; y_max += 1
    x_range = x_max - x_min or 1
    y_range = y_max - y_min or 1

    plot_w = width - 80
    plot_h = height - 100
    pad_l, pad_r, pad_t, pad_b = 60, 20, 50, 50

    font = _pil_font(11)
    title_font = _pil_font(14)

    img = Image.new("RGB", (width, height), theme.background.to_hex())
    d = ImageDraw.Draw(img)

    if title:
        tw, th = _text_size(d, title, title_font)
        d.text(((width - tw) / 2, 12), title, fill=theme.text.to_hex(), font=title_font)

    num_ticks = 5
    for i in range(num_ticks + 1):
        val = y_max - (y_max - y_min) * i / num_ticks
        y_pos = pad_t + plot_h - (plot_h * i / num_ticks)
        lbl = f"{val:,.0f}" if val == int(val) else f"{val:.1f}"
        tw, _ = _text_size(d, lbl, font)
        d.text((pad_l - tw - 6, y_pos - 6), lbl, fill=theme.text.to_hex(), font=font)
        d.line([pad_l, y_pos, pad_l + plot_w, y_pos], fill=theme.grid.to_hex(), width=1)

    r = 4
    for i, (x, y) in enumerate(pts):
        px = pad_l + (x - x_min) / x_range * plot_w
        py = pad_t + plot_h - (y - y_min) / y_range * plot_h
        c = theme.color_for(i)
        d.ellipse([px - r, py - r, px + r, py + r], fill=c.to_hex(), outline=theme.background.to_hex())

    idxs = [0, n // 2, n - 1]
    for i in idxs:
        if i >= n:
            continue
        x_pos = pad_l + (xs[i] - x_min) / x_range * plot_w
        lbl = f"{xs[i]:,.0f}" if xs[i] == int(xs[i]) else f"{xs[i]:.1f}"
        tw, _ = _text_size(d, lbl, font)
        d.text((x_pos - tw / 2, pad_t + plot_h + 4), lbl, fill=theme.text.to_hex(), font=font)

    d.line([pad_l, pad_t, pad_l, pad_t + plot_h], fill=theme.text.to_hex(), width=2)
    d.line([pad_l, pad_t + plot_h, pad_l + plot_w, pad_t + plot_h], fill=theme.text.to_hex(), width=2)

    if y_label:
        d.text((14, pad_t + plot_h / 2 - 6), y_label, fill=theme.text.to_hex(), font=font)

    return img


# ── Heatmap ───────────────────────────────────────────────────────────

def _render_heatmap(
    data: Data, x_col: str, y_col: str, v_col: str, theme: Theme,
    width: int = 800, height: int = 500, title: str = "",
) -> Image.Image:
    x_vals = data.column(x_col)
    y_vals = data.column(y_col)
    v_vals = data.column(v_col)
    n = len(x_vals)
    if n == 0:
        return _empty_image(width, height, theme, "No data")

    x_unique = sorted(set(x_vals))
    y_unique = sorted(set(y_vals), reverse=True)
    xn, yn = len(x_unique), len(y_unique)

    grid: dict[tuple, float] = {}
    for i in range(n):
        key = (x_vals[i], y_vals[i])
        grid[key] = v_vals[i]

    v_all = list(grid.values())
    v_min, v_max = min(v_all), max(v_all)
    v_range = v_max - v_min or 1

    cell_w = (width - 100) / xn
    cell_h = (height - 120) / yn
    font = _pil_font(9)
    title_font = _pil_font(14)

    img = Image.new("RGB", (width, height), theme.background.to_hex())
    d = ImageDraw.Draw(img)

    if title:
        tw, th = _text_size(d, title, title_font)
        d.text(((width - tw) / 2, 12), title, fill=theme.text.to_hex(), font=title_font)

    # Color legend
    legend_y = height - 20
    legend_w = 200
    legend_x = (width - legend_w) / 2
    grad = sequential_gradient(theme.primary, theme.accent, 20)
    for i, c in enumerate(grad):
        d.rectangle([int(legend_x + i * legend_w / 20), legend_y,
                      int(legend_x + (i + 1) * legend_w / 20), legend_y + 8],
                     fill=c.to_hex())

    d.text((legend_x, legend_y - 12), f"{v_min:.1f}", fill=theme.text.to_hex(), font=font)
    tw, _ = _text_size(d, f"{v_max:.1f}", font)
    d.text((legend_x + legend_w - tw, legend_y - 12), f"{v_max:.1f}", fill=theme.text.to_hex(), font=font)

    for j, yv in enumerate(y_unique):
        for i, xv in enumerate(x_unique):
            v = grid.get((xv, yv), 0)
            t = (v - v_min) / v_range
            r = int(theme.primary.r + (theme.accent.r - theme.primary.r) * t)
            g = int(theme.primary.g + (theme.accent.g - theme.primary.g) * t)
            b = int(theme.primary.b + (theme.accent.b - theme.primary.b) * t)
            c = Color(r, g, b)
            d.rectangle([int(i * cell_w), int(j * cell_h),
                          int((i + 1) * cell_w), int((j + 1) * cell_h)],
                         fill=c.to_hex(), outline=theme.grid.to_hex())
            # label
            if xn <= 20:
                tw, th = _text_size(d, str(xv), font)
                d.text((i * cell_w + cell_w / 2 - tw / 2, j * cell_h + cell_h / 2 - th / 2),
                       str(xv), fill=theme.text.to_hex() if t < 0.5 else Color(255, 255, 255).to_hex(),
                       font=font)

    # Y axis labels
    for j, yv in enumerate(y_unique):
        tw, th = _text_size(d, str(yv), font)
        d.text((width - 80 - tw, j * cell_h + cell_h / 2 - th / 2), str(yv),
               fill=theme.text.to_hex(), font=font)

    return img


# ── Pie chart ─────────────────────────────────────────────────────────

def _render_pie(
    data: Data, label_col: str, value_col: str, theme: Theme,
    width: int = 600, height: int = 500, title: str = "",
) -> Image.Image:
    vals_v = data.column(value_col)
    vals_l = data.column(label_col) if label_col in data.columns else []
    n = len(vals_v)
    if n == 0:
        return _empty_image(width, height, theme, "No data")

    total = sum(vals_v)
    if total == 0:
        return _empty_image(width, height, theme, "Values sum to zero")

    cx, cy = width / 2, height / 2
    radius = min(cx, cy) - 60
    font = _pil_font(10)
    title_font = _pil_font(14)

    img = Image.new("RGB", (width, height), theme.background.to_hex())
    d = ImageDraw.Draw(img)

    if title:
        tw, th = _text_size(d, title, title_font)
        d.text(((width - tw) / 2, 12), title, fill=theme.text.to_hex(), font=title_font)

    start_angle = 90
    for i, v in enumerate(vals_v):
        angle = v / total * 360
        end_angle = start_angle + angle
        c = theme.color_for(i)

        # arc
        box = [cx - radius, cy - radius, cx + radius, cy + radius]
        d.pieslice(box, start_angle, end_angle, fill=c.to_hex(), outline=theme.background.to_hex())

        # label
        mid = math.radians(start_angle + angle / 2)
        lx = cx + (radius + 15) * math.cos(mid)
        ly = cy + (radius + 15) * math.sin(mid)
        pct = v / total * 100
        lbl = f"{vals_l[i] if i < len(vals_l) else f'Item {i+1}'} {pct:.1f}%"
        tw, th = _text_size(d, lbl, font)
        d.text((lx - tw / 2, ly - th / 2), lbl, fill=theme.text.to_hex(), font=font)

        start_angle = end_angle

    return img


# ── Save helpers ──────────────────────────────────────────────────────

def _empty_image(width: int, height: int, theme: Theme, message: str) -> Image.Image:
    img = Image.new("RGB", (width, height), theme.background.to_hex())
    d = ImageDraw.Draw(img)
    font = _pil_font(14)
    tw, th = _text_size(d, message, font)
    d.text(((width - tw) / 2, height / 2 - th / 2), message, fill=theme.text.to_hex(), font=font)
    return img


def save_svg(chart_img: Image.Image, path: str | Path) -> None:
    """Save chart as PNG (SVG generation requires external lib; PNG is the fallback)."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    chart_img.save(str(path), format="PNG")


def save_png(chart_img: Image.Image, path: str | Path) -> None:
    """Save chart as PNG."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    chart_img.save(str(path), format="PNG", optimize=True)


# ── Public API ────────────────────────────────────────────────────────

@dataclass
class Chart:
    """A chart built from Data."""

    data: Data
    kind: str = "bar"  # bar | line | scatter | heatmap | pie
    x: str = "x"
    y: str = "y"
    label: str = ""
    theme: Theme = field(default_factory=Theme.light)
    title: str = ""
    width: int = 800
    height: int = 450

    def render(self) -> Image.Image:
        if self.kind == "bar":
            return _render_bar(self.data, self.x, self.y, self.theme,
                               self.width, self.height, self.title, self.label)
        elif self.kind == "line":
            return _render_line(self.data, self.x, self.y, self.theme,
                                self.width, self.height, self.title, self.label)
        elif self.kind == "scatter":
            return _render_scatter(self.data, self.x, self.y, self.theme,
                                   self.width, self.height, self.title, self.label)
        elif self.kind == "heatmap":
            # heatmap needs x, y, v columns
            return _render_heatmap(self.data, self.x, self.y, self.y, self.theme,
                                   self.width, self.height, self.title)
        elif self.kind == "pie":
            return _render_pie(self.data, self.x, self.y, self.theme,
                               self.width, self.height, self.title)
        else:
            raise ValueError(f"Unknown chart type: {self.kind}")

    def save(self, path: str | Path) -> None:
        img = self.render()
        ext = Path(path).suffix.lower()
        if ext in (".png", ".svg"):
            save_png(img, path)
        else:
            save_png(img, Path(path).with_suffix(".png"))

    def to_png_bytes(self) -> bytes:
        buf = BytesIO()
        self.render().save(buf, format="PNG")
        return buf.getvalue()

# Backward-compat alias
def save_chart(chart_img: Image.Image, path: str | Path) -> None:
    """Save a chart image to a file (PNG format)."""
    save_png(chart_img, path)
