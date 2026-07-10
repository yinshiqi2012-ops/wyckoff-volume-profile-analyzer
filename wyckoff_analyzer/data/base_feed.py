"""Abstract market data feed."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import pandas as pd


REQUIRED_COLUMNS = ("date", "open", "high", "low", "close", "volume")


def normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names and types to the project OHLCV contract."""
    if df is None or df.empty:
        return pd.DataFrame(columns=list(REQUIRED_COLUMNS))

    out = df.copy()
    rename = {}
    if "trade_date" in out.columns and "date" not in out.columns:
        rename["trade_date"] = "date"
    if "vol" in out.columns and "volume" not in out.columns:
        rename["vol"] = "volume"
    if rename:
        out = out.rename(columns=rename)

    missing = [c for c in REQUIRED_COLUMNS if c not in out.columns]
    if missing:
        raise ValueError(f"Missing OHLCV columns: {missing}")

    out = out[list(REQUIRED_COLUMNS)].copy()
    out["date"] = out["date"].astype(str).str.replace("-", "", regex=False)
    for col in ("open", "high", "low", "close", "volume"):
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=["open", "high", "low", "close", "volume"])
    out = out.sort_values("date").reset_index(drop=True)
    return out


class BaseFeed(ABC):
    @abstractmethod
    def fetch(
        self,
        symbol: str,
        count: Optional[int] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        """Return normalized OHLCV DataFrame."""
