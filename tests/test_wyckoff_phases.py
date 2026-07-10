"""Tests for Wyckoff phase and Spring/Upthrust detection."""

from __future__ import annotations

import pandas as pd
import pytest

from wyckoff_analyzer.core.wyckoff_phases import (
    detect_spring,
    detect_upthrust,
    detect_wyckoff_phase,
)


def _df(rows):
    return pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "volume"])


def test_spring_recovers_within_three_bars_with_shallow_depth():
    # Range ~10–11, then brief dip to 9.85 and recover
    rows = []
    for i in range(15):
        rows.append((f"d{i}", 10.5, 11.0, 10.0, 10.5, 100))
    # break day
    rows.append(("break", 10.0, 10.2, 9.85, 9.95, 90))
    # recover within 3
    rows.append(("r1", 10.0, 10.4, 9.9, 10.2, 80))
    df = _df(rows)
    event = detect_spring(df, support=10.0, recover_bars=3, max_depth_pct=0.02)
    assert event is not None
    assert event.kind == "SPRING"
    assert event.price == pytest.approx(9.85)


def test_spring_rejects_deep_break():
    rows = []
    for i in range(15):
        rows.append((f"d{i}", 10.5, 11.0, 10.0, 10.5, 100))
    rows.append(("break", 10.0, 10.1, 9.5, 9.6, 90))  # 5% deep
    rows.append(("r1", 9.8, 10.3, 9.7, 10.2, 80))
    df = _df(rows)
    event = detect_spring(df, support=10.0, recover_bars=3, max_depth_pct=0.02)
    assert event is None


def test_upthrust_fails_back_below_resistance():
    rows = []
    for i in range(15):
        rows.append((f"d{i}", 10.5, 11.0, 10.0, 10.5, 100))
    rows.append(("break", 11.0, 11.15, 10.9, 11.1, 150))
    rows.append(("fail", 11.0, 11.05, 10.7, 10.8, 120))
    df = _df(rows)
    event = detect_upthrust(df, resistance=11.0, recover_bars=3, max_depth_pct=0.02)
    assert event is not None
    assert event.kind == "UPTHRUST"


def test_markup_phase_on_higher_highs_and_volume():
    rows = []
    price = 10.0
    for i in range(20):
        price += 0.3
        rows.append((f"d{i}", price, price + 0.2, price - 0.1, price + 0.1, 150 + i * 5))
    df = _df(rows)
    result = detect_wyckoff_phase(df)
    assert result.phase in {"MARKUP", "ACCUMULATION"}
    assert result.score >= 0.5


def test_phase_markdown_when_close_below_val():
    rows = []
    for i in range(25):
        # drifting lower
        p = 12.0 - i * 0.15
        rows.append((f"d{i}", p, p + 0.2, p - 0.2, p - 0.05, 120))
    df = _df(rows)
    result = detect_wyckoff_phase(df, support=11.0, resistance=13.0)
    assert result.phase == "MARKDOWN"
    assert result.score < 0
