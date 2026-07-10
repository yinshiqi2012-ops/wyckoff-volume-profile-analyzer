"""Signal matrix and key-level construction."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

from wyckoff_analyzer.core.volume_profile import VolumeProfileResult
from wyckoff_analyzer.core.wyckoff_phases import PhaseResult, WyckoffEvent


@dataclass
class Signal:
    type: str
    trigger: str
    entry: float
    stop_loss: float
    target_1: float
    target_2: float
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Backward-compatible alias
TradeSignal = Signal


@dataclass
class KeyLevels:
    strong_resistance: List[float] = field(default_factory=list)
    moderate_resistance: List[float] = field(default_factory=list)
    poc: float = 0.0
    moderate_support: List[float] = field(default_factory=list)
    strong_support: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _round_levels(levels: List[float], ndigits: int = 2) -> List[float]:
    seen = set()
    out: List[float] = []
    for x in sorted(levels, reverse=True):
        r = round(float(x), ndigits)
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def build_key_levels(
    vp: VolumeProfileResult,
    events: List[WyckoffEvent],
    prior_high: Optional[float] = None,
    prior_low: Optional[float] = None,
) -> KeyLevels:
    spring_prices = [e.price for e in events if e.kind == "SPRING"]
    upthrust_prices = [e.price for e in events if e.kind == "UPTHRUST"]

    strong_res = [vp.vah] + upthrust_prices
    if prior_high is not None:
        strong_res.append(prior_high)

    strong_sup = [vp.val] + spring_prices
    if prior_low is not None:
        strong_sup.append(prior_low)

    mod_res = [p for p in vp.hvn if p > vp.poc] + [p for p in vp.lvn if p > vp.poc]
    mod_sup = [p for p in vp.hvn if p < vp.poc] + [p for p in vp.lvn if p < vp.poc]

    return KeyLevels(
        strong_resistance=_round_levels(strong_res),
        moderate_resistance=_round_levels(mod_res),
        poc=round(vp.poc, 2),
        moderate_support=_round_levels(mod_sup),
        strong_support=_round_levels(strong_sup),
    )


def _next_hvn_above(vp: VolumeProfileResult, price: float) -> float:
    above = sorted(p for p in vp.hvn if p > price)
    if above:
        return above[0]
    return vp.vah if vp.vah > price else price * 1.05


def _next_hvn_below(vp: VolumeProfileResult, price: float) -> float:
    below = sorted((p for p in vp.hvn if p < price), reverse=True)
    if below:
        return below[0]
    return vp.val if vp.val < price else price * 0.95


def generate_signals(
    df: pd.DataFrame,
    vp: VolumeProfileResult,
    phase: PhaseResult,
) -> List[Signal]:
    """Map phase + events + VP levels into the C1 signal matrix."""
    if df is None or df.empty:
        return []

    close = float(df["close"].iloc[-1])
    recent_vol = float(df["volume"].tail(5).mean())
    avg_vol = float(df["volume"].tail(20).mean()) if len(df) >= 5 else recent_vol
    shrinking = avg_vol > 0 and recent_vol < avg_vol * 0.9
    expanding = avg_vol > 0 and recent_vol > avg_vol * 1.1

    kinds = {e.kind for e in phase.events}
    spring = next((e for e in phase.events if e.kind == "SPRING"), None)
    upthrust = next((e for e in phase.events if e.kind == "UPTHRUST"), None)
    signals: List[Signal] = []

    if (
        phase.phase == "ACCUMULATION"
        and spring is not None
        and close > vp.val
        and shrinking
    ):
        stop = min(spring.price, vp.val) * 0.99
        t1 = vp.vah
        t2 = _next_hvn_above(vp, vp.vah)
        signals.append(
            Signal(
                type="STRONG_BUY",
                trigger="Spring + Back above VAL + shrinking volume",
                entry=round(close, 2),
                stop_loss=round(stop, 2),
                target_1=round(t1, 2),
                target_2=round(t2, 2),
                confidence=0.85,
            )
        )

    if "SOS" in kinds and close >= vp.poc and shrinking:
        stop = min(vp.poc, vp.val) * 0.99
        signals.append(
            Signal(
                type="BUY",
                trigger="SOS breakout + pullback context near POC/VAH",
                entry=round(close, 2),
                stop_loss=round(stop, 2),
                target_1=round(_next_hvn_above(vp, close), 2),
                target_2=round(_next_hvn_above(vp, close) * 1.02, 2),
                confidence=0.65,
            )
        )

    if (
        phase.phase == "DISTRIBUTION"
        and upthrust is not None
        and close < vp.poc
        and expanding
    ):
        stop = max(upthrust.price, vp.vah) * 1.01
        t1 = vp.val
        t2 = _next_hvn_below(vp, vp.val)
        signals.append(
            Signal(
                type="STRONG_SELL",
                trigger="Upthrust + Below POC + expanding volume",
                entry=round(close, 2),
                stop_loss=round(stop, 2),
                target_1=round(t1, 2),
                target_2=round(t2, 2),
                confidence=0.85,
            )
        )

    if "SOW" in kinds and close <= vp.poc and shrinking:
        stop = max(vp.poc, vp.vah) * 1.01
        signals.append(
            Signal(
                type="SELL",
                trigger="SOW breakdown + bounce context near VAL/POC",
                entry=round(close, 2),
                stop_loss=round(stop, 2),
                target_1=round(_next_hvn_below(vp, close), 2),
                target_2=round(_next_hvn_below(vp, close) * 0.98, 2),
                confidence=0.65,
            )
        )

    if not signals and vp.val <= close <= vp.vah and not kinds.intersection(
        {"SPRING", "UPTHRUST", "SOS", "SOW"}
    ):
        signals.append(
            Signal(
                type="WATCH",
                trigger="Price inside ValueArea without clear Wyckoff event",
                entry=round(close, 2),
                stop_loss=round(vp.val * 0.98, 2),
                target_1=round(vp.vah, 2),
                target_2=round(_next_hvn_above(vp, vp.vah), 2),
                confidence=0.30,
            )
        )

    if not signals:
        signals.append(
            Signal(
                type="WATCH",
                trigger=f"Phase={phase.phase}; no matrix match",
                entry=round(close, 2),
                stop_loss=round(min(close, vp.val) * 0.98, 2),
                target_1=round(max(close, vp.vah), 2),
                target_2=round(_next_hvn_above(vp, max(close, vp.vah)), 2),
                confidence=0.30,
            )
        )

    return signals
