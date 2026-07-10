"""Tests for Volume Profile engine."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from wyckoff_analyzer.core.volume_profile import (
    UniformAllocation,
    calc_volume_profile,
)


def _bars(rows):
    return pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "volume"])


def test_poc_is_price_bin_with_highest_volume():
    # Three bars stacked on 10–11 so that band gets most volume
    df = _bars(
        [
            ("2026-01-01", 10.5, 11.0, 10.0, 10.8, 100),
            ("2026-01-02", 10.6, 11.0, 10.0, 10.7, 100),
            ("2026-01-03", 12.0, 13.0, 12.0, 12.5, 10),
        ]
    )
    result = calc_volume_profile(df, num_bins=20)
    assert 10.0 <= result.poc <= 11.0
    assert result.total_volume == pytest.approx(210)


def test_value_area_is_contiguous_band_around_poc():
    df = _bars(
        [
            ("2026-01-01", 10.0, 10.5, 9.5, 10.0, 50),
            ("2026-01-02", 10.2, 10.8, 9.8, 10.3, 80),
            ("2026-01-03", 10.5, 11.0, 10.0, 10.6, 100),
            ("2026-01-04", 11.0, 12.0, 10.5, 11.5, 40),
            ("2026-01-05", 12.0, 13.0, 11.5, 12.5, 20),
        ]
    )
    result = calc_volume_profile(df, num_bins=50)
    assert result.val <= result.poc <= result.vah
    # VA should cover a meaningful share of volume (POC-expansion to 70%)
    assert result.vah > result.val


def test_uniform_allocation_spreads_volume_across_touched_bins():
    alloc = UniformAllocation()
    parts = alloc.allocate(
        low=10.0,
        high=12.0,
        close=11.0,
        volume=100.0,
        price_min=10.0,
        bin_size=1.0,
        num_bins=3,
    )
    # bins covering 10-11, 11-12, and possibly edge
    assert sum(parts.values()) == pytest.approx(100.0)
    assert len(parts) >= 2
    assert len(set(round(v, 6) for v in parts.values())) == 1


def test_hvn_detected_at_local_peak():
    # Construct profile indirectly: many bars in a narrow band, sparse elsewhere
    rows = []
    for i in range(20):
        rows.append((f"2026-01-{i+1:02d}", 10.0, 10.2, 9.8, 10.0, 100))
    for i in range(5):
        rows.append((f"2026-02-{i+1:02d}", 12.0, 12.5, 11.5, 12.0, 5))
    df = _bars(rows)
    result = calc_volume_profile(df, num_bins=40, neighbor_n=2, hvn_multiplier=1.5)
    assert len(result.hvn) >= 1
    # Dense volume sits near 10; at least one HVN should be in that region
    assert any(9.5 <= p <= 10.5 for p in result.hvn)


def test_empty_dataframe_raises():
    with pytest.raises(ValueError):
        calc_volume_profile(pd.DataFrame())
