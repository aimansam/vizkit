"""Data loading from CSV and JSON files."""
from __future__ import annotations
import csv
import json
from pathlib import Path
from typing import Any


class Data:
    """Numeric columnar data loaded from CSV or JSON.

    Examples
    --------
    >>> d = Data.from_csv("sales.csv")
    >>> d = Data.from_json("points.json")
    """

    def __init__(self, columns: dict[str, list[float | int | str]], labels: list[str] | None = None):
        self.columns = {k: list(v) for k, v in columns.items()}
        self.labels = labels or []
        self._numeric: dict[str, list[float]] | None = None

    @classmethod
    def from_csv(cls, path: str | Path) -> "Data":
        p = Path(path)
        with p.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        if not rows:
            return cls({}, [])
        keys = list(rows[0].keys())
        cols: dict[str, list] = {k: [] for k in keys}
        for row in rows:
            for k in keys:
                v = row.get(k, "")
                cols[k].append(v)
        return cls(cols, labels=rows[0].get("label", "") and [r.get("label", "") for r in rows] or None)

    @classmethod
    def from_json(cls, path: str | Path) -> "Data":
        p = Path(path)
        obj = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(obj, list):
            if not obj:
                return cls({}, [])
            keys = list(obj[0].keys())
            cols: dict[str, list] = {k: [] for k in keys}
            for item in obj:
                for k in keys:
                    cols[k].append(item.get(k, ""))
            return cls(cols)
        if isinstance(obj, dict):
            cols: dict[str, list] = {}
            for k, v in obj.items():
                if isinstance(v, list):
                    cols[k] = list(v)
                else:
                    cols[k] = [v]
            return cls(cols)
        return cls({}, [])

    @property
    def numeric(self) -> dict[str, list[float]]:
        if self._numeric is None:
            self._numeric = {}
            for k, vals in self.columns.items():
                nums = []
                for v in vals:
                    try:
                        nums.append(float(v))
                    except (ValueError, TypeError):
                        nums.append(0.0)
                self._numeric[k] = nums
        return self._numeric

    def column(self, name: str) -> list[float]:
        return self.numeric.get(name, [])

    def pairs(self, x: str, y: str) -> list[tuple[float, float]]:
        xs = self.numeric.get(x, [])
        ys = self.numeric.get(y, [])
        n = min(len(xs), len(ys))
        return list(zip(xs[:n], ys[:n]))

    @property
    def shape(self) -> tuple[int, int]:
        if not self.columns:
            return (0, 0)
        return (len(next(iter(self.columns.values()))), len(self.columns))

    def __repr__(self) -> str:
        return f"Data(shape={self.shape}, cols={list(self.columns.keys())})"
