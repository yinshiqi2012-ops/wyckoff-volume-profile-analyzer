"""Market structure helpers: swings, range bounds, trend features."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SwingPoint:
    index: int
    price: float
    kind: str  # "high" | "low"


def find_swing_points(df: pd.DataFrame, radius: int = 3) -> List[SwingPoint]:
    """Detect local swing highs/lows using a simple fractal window."""
    highs = df["high"].to_numpy(dtype=float)
    lows = df["low"].to_numpy(dtype=float)
    swings: List[SwingPoint] = []
    n = len(df)
    for i in range(radius, n - radius):
        window_h = highs[i - radius : i + radius + 1]
        window_l = lows[i - radius : i + radius + 1]
        if highs[i] == window_h.max() and np.sum(window_h == highs[i]) == 1:
            swings.append(SwingPoint(i, float(highs[i]), "high"))
        if lows[i] == window_l.min() and np.sum(window_l == lows[i]) == 1:
            swings.append(SwingPoint(i, float(lows[i]), "low"))
    return swings


def trading_range(df: pd.DataFrame) -> Tuple[float, float]:
    """Return (range_low, range_high) for the window."""
    return float(df["low"].min()), float(df["high"].max())


def higher_highs_lows_counts(df: pd.DataFrame) -> Tuple[int, int, int, int]:
    """Count consecutive-style HH/HL/LH/LL comparisons on successive bars."""
    highs = df["high"].to_numpy(dtype=float)
    lows = df["low"].to_numpy(dtype=float)
    hh = hl = lh = ll = 0
    for i in range(1, len(highs)):
        if highs[i] > highs[i - 1]:
            hh += 1
        if lows[i] > lows[i - 1]:
            hl += 1
        if highs[i] < highs[i - 1]:
            lh += 1
        if lows[i] < lows[i - 1]:
            ll += 1
    return hh, hl, lh, ll


def range_pct(df: pd.DataFrame) -> float:
    lo, hi = trading_range(df)
    if lo <= 0:
        return 0.0
    return (hi - lo) / lo


def avg_volume(df: pd.DataFrame, n: Optional[int] = None) -> float:
    series = df["volume"] if n is None else df["volume"].tail(n)
    return float(series.mean()) if len(series) else 0.0
