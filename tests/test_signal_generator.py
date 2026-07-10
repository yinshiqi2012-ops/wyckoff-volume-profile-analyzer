"""Tests for signal matrix."""

from __future__ import annotations

import pandas as pd

from wyckoff_analyzer.core.signal_generator import generate_signals
from wyckoff_analyzer.core.volume_profile import VolumeProfileResult
from wyckoff_analyzer.core.wyckoff_phases import PhaseResult, WyckoffEvent


def _vp(**kwargs):
    base = dict(
        poc=11.0,
        vah=12.0,
        val=10.0,
        profile={10.0: 1, 11.0: 5, 12.0: 1},
        hvn=[10.0, 11.0, 12.5],
        lvn=[10.5],
        bin_size=0.1,
        total_volume=100,
    )
    base.update(kwargs)
    return VolumeProfileResult(**base)


def _df(close=11.2, volume=80):
    rows = []
    for i in range(25):
        rows.append(
            {
                "date": f"d{i}",
                "open": 11.0,
                "high": 11.5,
                "low": 10.5,
                "close": 11.0,
                "volume": 100,
            }
        )
    rows[-1]["close"] = close
    rows[-1]["volume"] = volume
    for i in range(-5, 0):
        rows[i]["volume"] = volume
    return pd.DataFrame(rows)


def test_strong_buy_on_accumulation_spring_above_val():
    phase = PhaseResult(
        phase="ACCUMULATION",
        confidence=0.8,
        score=0.5,
        events=[WyckoffEvent("SPRING", 20, 9.9)],
    )
    signals = generate_signals(_df(close=11.2, volume=70), _vp(), phase)
    assert signals[0].type == "STRONG_BUY"
    assert signals[0].confidence == 0.85
    assert signals[0].stop_loss < signals[0].entry


def test_watch_inside_value_area_without_events():
    phase = PhaseResult("CONSOLIDATION", 0.4, 0.0, [])
    signals = generate_signals(_df(close=11.0, volume=100), _vp(), phase)
    assert signals[0].type == "WATCH"
