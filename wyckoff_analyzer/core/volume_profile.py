"""Volume Profile engine: POC, ValueArea, HVN/LVN."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class VolumeProfileResult:
    poc: float
    vah: float
    val: float
    profile: Dict[float, float]
    hvn: List[float]
    lvn: List[float]
    bin_size: float
    total_volume: float


class VolumeAllocation(ABC):
    """Strategy that maps a single Bar's volume onto price bins."""

    @abstractmethod
    def allocate(
        self,
        low: float,
        high: float,
        close: float,
        volume: float,
        price_min: float,
        bin_size: float,
        num_bins: int,
    ) -> Dict[int, float]:
        """Return {bin_index: volume_portion}."""


class UniformAllocation(VolumeAllocation):
    """Spread volume evenly across bins touched by high–low."""

    def allocate(
        self,
        low: float,
        high: float,
        close: float,
        volume: float,
        price_min: float,
        bin_size: float,
        num_bins: int,
    ) -> Dict[int, float]:
        if volume <= 0 or bin_size <= 0 or high < low:
            return {}
        low_bin = int((low - price_min) / bin_size)
        high_bin = int((high - price_min) / bin_size)
        low_bin = max(0, min(num_bins - 1, low_bin))
        high_bin = max(0, min(num_bins - 1, high_bin))
        if high_bin < low_bin:
            low_bin, high_bin = high_bin, low_bin
        n = high_bin - low_bin + 1
        portion = volume / n
        return {b: portion for b in range(low_bin, high_bin + 1)}


def _bin_center(price_min: float, bin_index: int, bin_size: float) -> float:
    return price_min + bin_index * bin_size + bin_size / 2.0


def _expand_value_area(
    volumes: np.ndarray,
    poc_index: int,
    target_volume: float,
) -> Tuple[int, int]:
    """Expand from POC until cumulative volume >= target. Returns (low_idx, high_idx)."""
    n = len(volumes)
    low_i = high_i = poc_index
    cumulative = float(volumes[poc_index])
    if cumulative >= target_volume:
        return low_i, high_i

    while cumulative < target_volume and (low_i > 0 or high_i < n - 1):
        up_vol = float(volumes[high_i + 1]) if high_i < n - 1 else -1.0
        down_vol = float(volumes[low_i - 1]) if low_i > 0 else -1.0

        if up_vol < 0 and down_vol < 0:
            break
        if up_vol >= down_vol:
            high_i += 1
            cumulative += up_vol
        else:
            low_i -= 1
            cumulative += down_vol

    return low_i, high_i


def _local_peak_nodes(
    prices: Sequence[float],
    volumes: np.ndarray,
    neighbor_n: int = 2,
    hvn_multiplier: float = 1.5,
    lvn_multiplier: float = 0.5,
) -> Tuple[List[float], List[float]]:
    hvn: List[float] = []
    lvn: List[float] = []
    n = len(volumes)
    for i in range(n):
        left = max(0, i - neighbor_n)
        right = min(n, i + neighbor_n + 1)
        neighbors = [volumes[j] for j in range(left, right) if j != i]
        if not neighbors:
            continue
        mean_n = float(np.mean(neighbors))
        if mean_n <= 0:
            continue
        ratio = float(volumes[i]) / mean_n
        if ratio >= hvn_multiplier:
            hvn.append(float(prices[i]))
        elif ratio <= lvn_multiplier:
            lvn.append(float(prices[i]))
    return hvn, lvn


def calc_volume_profile(
    df: pd.DataFrame,
    num_bins: int = 100,
    value_area_pct: float = 0.70,
    allocation: Optional[VolumeAllocation] = None,
    neighbor_n: int = 2,
    hvn_multiplier: float = 1.5,
    lvn_multiplier: float = 0.5,
) -> VolumeProfileResult:
    """Compute Volume Profile for an AnalysisWindow DataFrame.

    Required columns: high, low, close, volume.
    """
    if df is None or df.empty:
        raise ValueError("DataFrame is empty")
    required = {"high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    allocation = allocation or UniformAllocation()
    price_min = float(df["low"].min())
    price_max = float(df["high"].max())
    if price_max <= price_min:
        # Degenerate flat range: single bin
        bin_size = max(abs(price_min) * 1e-6, 1e-8)
        price_max = price_min + bin_size
        num_bins = 1
    else:
        bin_size = (price_max - price_min) / num_bins

    volumes = np.zeros(num_bins, dtype=float)
    for row in df.itertuples(index=False):
        parts = allocation.allocate(
            low=float(row.low),
            high=float(row.high),
            close=float(row.close),
            volume=float(row.volume),
            price_min=price_min,
            bin_size=bin_size,
            num_bins=num_bins,
        )
        for b, v in parts.items():
            volumes[b] += v

    total_volume = float(volumes.sum())
    if total_volume <= 0:
        raise ValueError("Total volume is zero")

    poc_index = int(np.argmax(volumes))
    prices = [_bin_center(price_min, i, bin_size) for i in range(num_bins)]
    poc = prices[poc_index]

    low_i, high_i = _expand_value_area(
        volumes, poc_index, total_volume * value_area_pct
    )
    val = prices[low_i] - bin_size / 2.0
    vah = prices[high_i] + bin_size / 2.0
    # Clamp to observed range edges for readability
    val = max(price_min, val)
    vah = min(price_max, vah)

    hvn, lvn = _local_peak_nodes(
        prices,
        volumes,
        neighbor_n=neighbor_n,
        hvn_multiplier=hvn_multiplier,
        lvn_multiplier=lvn_multiplier,
    )

    profile = {prices[i]: float(volumes[i]) for i in range(num_bins) if volumes[i] > 0}

    return VolumeProfileResult(
        poc=float(poc),
        vah=float(vah),
        val=float(val),
        profile=profile,
        hvn=hvn,
        lvn=lvn,
        bin_size=float(bin_size),
        total_volume=total_volume,
    )
