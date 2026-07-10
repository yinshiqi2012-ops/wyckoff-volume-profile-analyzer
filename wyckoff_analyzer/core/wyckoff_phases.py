"""Wyckoff phase and event detection (MVP: 4 phases + Spring/Upthrust)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import pandas as pd

from wyckoff_analyzer.core.market_structure import (
    avg_volume,
    higher_highs_lows_counts,
    range_pct,
    trading_range,
)


PHASES = (
    "ACCUMULATION",
    "MARKUP",
    "DISTRIBUTION",
    "MARKDOWN",
    "CONSOLIDATION",
)


@dataclass(frozen=True)
class WyckoffEvent:
    kind: str  # SPRING | UPTHRUST | SOS | SOW
    index: int
    price: float
    detail: str = ""


@dataclass(frozen=True)
class PhaseResult:
    phase: str
    confidence: float
    score: float  # -2..2 style index for charting
    events: List[WyckoffEvent] = field(default_factory=list)


def detect_wyckoff_phase(
    df: pd.DataFrame,
    window: Optional[int] = None,
    support: Optional[float] = None,
    resistance: Optional[float] = None,
) -> PhaseResult:
    """Simplified phase detection from price structure + volume.

    Optional support/resistance (typically VAL/VAH) improve Spring/Upthrust
    and bias Markup/Markdown when price has left the ValueArea.
    """
    if df is None or len(df) < 5:
        return PhaseResult("CONSOLIDATION", 0.3, 0.0, [])

    bars = df if window is None else df.tail(window)
    hh, hl, lh, ll = higher_highs_lows_counts(bars)
    n = max(len(bars) - 1, 1)
    avg_vol = avg_volume(bars)
    recent_vol = avg_volume(bars, 5)
    rp = range_pct(bars)
    close = float(bars["close"].iloc[-1])

    events = detect_events(df, support=support, resistance=resistance)

    # Price relative to ValueArea edges (when provided)
    below_val = support is not None and close < support
    above_vah = resistance is not None and close > resistance

    # Structure-dominant
    if hh / n > 0.55 and hl / n > 0.55:
        if above_vah or recent_vol > avg_vol * 1.15:
            return PhaseResult("MARKUP", 0.78 if above_vah else 0.75, 2.0, events)
        return PhaseResult("ACCUMULATION", 0.65, 1.0, events)

    if lh / n > 0.55 and ll / n > 0.55:
        if below_val or recent_vol > avg_vol * 1.15:
            return PhaseResult("MARKDOWN", 0.78 if below_val else 0.75, -2.0, events)
        return PhaseResult("DISTRIBUTION", 0.65, -1.0, events)

    # Broken out of VA without strict HH/HL counts
    if below_val and ll >= lh:
        return PhaseResult("MARKDOWN", 0.7, -2.0, events)
    if above_vah and hh >= hl:
        return PhaseResult("MARKUP", 0.7, 2.0, events)

    # Range-bound
    if rp < 0.08:
        if recent_vol < avg_vol * 0.85:
            conf = 0.7 if any(e.kind == "SPRING" for e in events) else 0.55
            return PhaseResult("ACCUMULATION", conf, 0.5, events)
        if recent_vol > avg_vol * 1.1:
            conf = 0.7 if any(e.kind == "UPTHRUST" for e in events) else 0.55
            return PhaseResult("DISTRIBUTION", conf, -0.5, events)

    # Event bias
    if any(e.kind == "SPRING" for e in events):
        return PhaseResult("ACCUMULATION", 0.72, 0.5, events)
    if any(e.kind == "UPTHRUST" for e in events):
        return PhaseResult("DISTRIBUTION", 0.72, -0.5, events)

    return PhaseResult("CONSOLIDATION", 0.4, 0.0, events)


def detect_spring(
    df: pd.DataFrame,
    support: float,
    recover_bars: int = 3,
    max_depth_pct: float = 0.02,
    vol_cap_mult: float = 1.1,
    vol_window: int = 20,
) -> Optional[WyckoffEvent]:
    """Strict Spring: break support, recover within N bars, depth ≤ 2%, non-expanding vol."""
    if df is None or len(df) < recover_bars + 1 or support <= 0:
        return None

    avg_vol = avg_volume(df, vol_window)
    # Scan recent window for a break that recovers
    start = max(0, len(df) - max(recover_bars + 5, 10))
    for i in range(start, len(df)):
        low = float(df["low"].iloc[i])
        if low >= support:
            continue
        depth = (support - low) / support
        if depth > max_depth_pct:
            continue
        vol_break = float(df["volume"].iloc[i])
        if avg_vol > 0 and vol_break > avg_vol * vol_cap_mult:
            continue
        # Must recover within recover_bars after the break
        end = min(len(df), i + recover_bars + 1)
        recovered = False
        for j in range(i, end):
            if float(df["close"].iloc[j]) > support:
                recovered = True
                break
        if recovered:
            return WyckoffEvent("SPRING", i, low, f"support={support:.4f}")
    return None


def detect_upthrust(
    df: pd.DataFrame,
    resistance: float,
    recover_bars: int = 3,
    max_depth_pct: float = 0.02,
    vol_cap_mult: float = 1.5,
    vol_window: int = 20,
) -> Optional[WyckoffEvent]:
    """Upthrust: brief break above resistance that fails within N bars."""
    if df is None or len(df) < recover_bars + 1 or resistance <= 0:
        return None

    avg_vol = avg_volume(df, vol_window)
    start = max(0, len(df) - max(recover_bars + 5, 10))
    for i in range(start, len(df)):
        high = float(df["high"].iloc[i])
        if high <= resistance:
            continue
        depth = (high - resistance) / resistance
        if depth > max_depth_pct:
            continue
        # Upthrust often prints expanding volume that cannot hold
        vol_break = float(df["volume"].iloc[i])
        # Prefer expanding volume, but do not hard-require if avg is tiny
        if avg_vol > 0 and vol_break < avg_vol * 0.8:
            continue
        end = min(len(df), i + recover_bars + 1)
        failed = False
        for j in range(i, end):
            if float(df["close"].iloc[j]) < resistance:
                failed = True
                break
        if failed:
            return WyckoffEvent("UPTHRUST", i, high, f"resistance={resistance:.4f}")
    return None


def detect_sos_sow(df: pd.DataFrame) -> List[WyckoffEvent]:
    """Simplified SOS/SOW: wide-range bar with volume expansion through range edge."""
    if len(df) < 10:
        return []
    lo, hi = trading_range(df.iloc[:-1])
    avg_vol = avg_volume(df.iloc[:-5], 20) or avg_volume(df)
    last = df.iloc[-1]
    rng = float(last.high) - float(last.low)
    body = abs(float(last.close) - float(last.open))
    typical = float((df["high"] - df["low"]).tail(20).mean())
    events: List[WyckoffEvent] = []
    if typical > 0 and rng > typical * 1.5 and float(last.volume) > avg_vol * 1.3:
        if float(last.close) > hi and float(last.close) > float(last.open):
            events.append(WyckoffEvent("SOS", len(df) - 1, float(last.close), "breakout"))
        if float(last.close) < lo and float(last.close) < float(last.open):
            events.append(WyckoffEvent("SOW", len(df) - 1, float(last.close), "breakdown"))
    return events


def detect_events(
    df: pd.DataFrame,
    support: Optional[float] = None,
    resistance: Optional[float] = None,
) -> List[WyckoffEvent]:
    """Detect Spring/Upthrust against VAL/VAH (preferred) or prior range."""
    if df is None or len(df) < 8:
        return []
    prior = df.iloc[:-3] if len(df) > 10 else df.iloc[:-1]
    range_low, range_high = trading_range(prior)
    # Prefer VP edges when provided; otherwise use prior swing range
    support_level = float(support) if support is not None else range_low
    resistance_level = float(resistance) if resistance is not None else range_high

    events: List[WyckoffEvent] = []
    spring = detect_spring(df, support_level)
    if spring:
        events.append(spring)
    upthrust = detect_upthrust(df, resistance_level)
    if upthrust:
        events.append(upthrust)
    events.extend(detect_sos_sow(df))
    return events
