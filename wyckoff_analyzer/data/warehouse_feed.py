"""DuckDB / local warehouse feed via WarehouseClient."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import pandas as pd

from wyckoff_analyzer.data.base_feed import BaseFeed, normalize_ohlcv


def _ensure_vibecoding_on_path() -> None:
    root = Path(__file__).resolve().parents[3]  # .../vibecoding
    # parents: data -> wyckoff_analyzer -> project -> vibecoding
    # Actually: .../Wyckoff Volume Profile Analyzer/wyckoff_analyzer/data/thisfile
    # parents[0]=data, [1]=wyckoff_analyzer, [2]=project, [3]=vibecoding
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    # Also try sibling default
    fallback = Path(r"D:\vibecoding")
    if fallback.is_dir() and str(fallback) not in sys.path:
        sys.path.insert(0, str(fallback))


class WarehouseFeed(BaseFeed):
    """Primary feed: local DuckDB (via WarehouseClient.daily)."""

    def __init__(self, warehouse_root: Optional[str] = None):
        _ensure_vibecoding_on_path()
        from data_warehouse import WarehouseClient

        self._client = WarehouseClient(root=warehouse_root)

    def fetch(
        self,
        symbol: str,
        count: Optional[int] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        df = self._client.daily(symbol, count=count, start=start, end=end)
        return normalize_ohlcv(df)
