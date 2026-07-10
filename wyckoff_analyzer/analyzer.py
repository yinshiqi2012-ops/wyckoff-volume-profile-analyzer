"""Public analyzer facade."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Optional

import pandas as pd

from wyckoff_analyzer.core.signal_generator import build_key_levels, generate_signals
from wyckoff_analyzer.core.volume_profile import VolumeAllocation, calc_volume_profile
from wyckoff_analyzer.core.wyckoff_phases import detect_wyckoff_phase
from wyckoff_analyzer.data.base_feed import normalize_ohlcv
from wyckoff_analyzer.data.composite_feed import CompositeFeed


class WyckoffAnalyzer:
    """Analyze an OHLCV window and return a structured report."""

    def __init__(
        self,
        df: pd.DataFrame,
        symbol: str = "",
        name: str = "",
        window: int = 60,
        num_bins: int = 100,
        allocation: Optional[VolumeAllocation] = None,
        data_source: Optional[str] = None,
    ):
        self.symbol = symbol
        self.name = name
        self.window = window
        self.num_bins = num_bins
        self.allocation = allocation
        self.data_source = data_source
        full = normalize_ohlcv(df)
        # If history is shorter than window (e.g. new listings), use all available bars
        self.df = full.tail(window).reset_index(drop=True) if window else full
        self.window = len(self.df)

    @classmethod
    def from_symbol(
        cls,
        symbol: str,
        window: int = 60,
        num_bins: int = 100,
        feed: Optional[CompositeFeed] = None,
        fetch_count: Optional[int] = None,
        name: Optional[str] = None,
    ) -> "WyckoffAnalyzer":
        from wyckoff_analyzer.data.symbol_names import resolve_name

        feed = feed or CompositeFeed()
        count = fetch_count or max(window + 40, 120)
        df = feed.fetch(symbol, count=count)
        if df.empty:
            raise ValueError(f"No data for symbol {symbol}")
        resolved = name if name is not None else resolve_name(symbol)
        return cls(
            df=df,
            symbol=symbol,
            name=resolved,
            window=window,
            num_bins=num_bins,
            data_source=feed.last_source,
        )

    def analyze(self) -> Dict[str, Any]:
        if self.df.empty:
            raise ValueError("No bars to analyze")

        vp = calc_volume_profile(
            self.df,
            num_bins=self.num_bins,
            allocation=self.allocation,
        )
        # Use VAL/VAH as Spring/Upthrust reference levels
        phase = detect_wyckoff_phase(self.df, support=vp.val, resistance=vp.vah)
        signals = generate_signals(self.df, vp, phase)
        prior_high = float(self.df["high"].max())
        prior_low = float(self.df["low"].min())
        levels = build_key_levels(
            vp,
            phase.events,
            prior_high=prior_high,
            prior_low=prior_low,
        )

        return {
            "symbol": self.symbol,
            "name": self.name,
            "data_source": self.data_source,
            "window": self.window,
            "bars": len(self.df),
            "current_phase": phase.phase,
            "phase_confidence": phase.confidence,
            "phase_score": phase.score,
            "recent_events": [
                {
                    "kind": e.kind,
                    "index": e.index,
                    "price": round(e.price, 4),
                    "detail": e.detail,
                }
                for e in phase.events
            ],
            "volume_profile": {
                "poc": round(vp.poc, 4),
                "vah": round(vp.vah, 4),
                "val": round(vp.val, 4),
                "hvn": [round(x, 4) for x in vp.hvn],
                "lvn": [round(x, 4) for x in vp.lvn],
                "bin_size": round(vp.bin_size, 6),
                "total_volume": round(vp.total_volume, 2),
            },
            "signals": [s.to_dict() for s in signals],
            "key_levels": levels.to_dict(),
            "last_close": round(float(self.df["close"].iloc[-1]), 4),
            "date_range": {
                "start": str(self.df["date"].iloc[0]),
                "end": str(self.df["date"].iloc[-1]),
            },
            # Internal objects for charting (not JSON-serialized by CLI)
            "_vp": vp,
            "_phase": phase,
            "_df": self.df,
        }
