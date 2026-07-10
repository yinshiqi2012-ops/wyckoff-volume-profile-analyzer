"""Composite feed: warehouse → local cache → Tushare → akshare → yfinance."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import pandas as pd

from wyckoff_analyzer.data.akshare_feed import AkshareFeed
from wyckoff_analyzer.data.base_feed import BaseFeed, normalize_ohlcv
from wyckoff_analyzer.data.csv_feed import CsvFeed
from wyckoff_analyzer.data.tushare_feed import TushareFeed
from wyckoff_analyzer.data.warehouse_feed import WarehouseFeed
from wyckoff_analyzer.data.yfinance_feed import YFinanceFeed


def _default_cache_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "data_cache"


class CompositeFeed(BaseFeed):
    """Try local warehouse first, then remote fallbacks."""

    def __init__(
        self,
        warehouse: Optional[WarehouseFeed] = None,
        tushare: Optional[TushareFeed] = None,
        akshare: Optional[AkshareFeed] = None,
        yfinance: Optional[YFinanceFeed] = None,
        enable_tushare_fallback: bool = True,
        cache_dir: Optional[Union[str, Path]] = None,
    ):
        self._warehouse = warehouse
        self._tushare = tushare
        self._akshare = akshare
        self._yfinance = yfinance
        self._enable_tushare_fallback = enable_tushare_fallback
        self._cache_dir = Path(cache_dir) if cache_dir else _default_cache_dir()
        self.last_source: Optional[str] = None

    def _get_warehouse(self) -> WarehouseFeed:
        if self._warehouse is None:
            self._warehouse = WarehouseFeed()
        return self._warehouse

    def _get_tushare(self) -> TushareFeed:
        if self._tushare is None:
            self._tushare = TushareFeed()
        return self._tushare

    def _get_akshare(self) -> AkshareFeed:
        if self._akshare is None:
            self._akshare = AkshareFeed()
        return self._akshare

    def _get_yfinance(self) -> YFinanceFeed:
        if self._yfinance is None:
            self._yfinance = YFinanceFeed()
        return self._yfinance

    def fetch(
        self,
        symbol: str,
        count: Optional[int] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        try:
            df = self._get_warehouse().fetch(symbol, count=count, start=start, end=end)
            if df is not None and not df.empty:
                self.last_source = "warehouse"
                return df
        except Exception:
            pass

        # Local CSV cache (e.g. data_cache/09992.HK.csv)
        cached = self._cache_path(symbol)
        if cached is not None:
            try:
                df = CsvFeed(cached).fetch(symbol, count=count, start=start, end=end)
                if df is not None and not df.empty:
                    self.last_source = "cache"
                    return df
            except Exception:
                pass

        if not self._enable_tushare_fallback:
            self.last_source = None
            return normalize_ohlcv(pd.DataFrame())

        # Remote chain — continue on rate-limit / network errors
        for name, getter in (
            ("tushare", self._get_tushare),
            ("akshare", self._get_akshare),
            ("yfinance", self._get_yfinance),
        ):
            try:
                df = getter().fetch(symbol, count=count, start=start, end=end)
                if df is not None and not df.empty:
                    self.last_source = name
                    return df
            except Exception:
                continue

        self.last_source = None
        return normalize_ohlcv(pd.DataFrame())

    def _cache_path(self, symbol: str) -> Optional[Path]:
        if not self._cache_dir.is_dir():
            return None
        sym = symbol.strip().upper()
        candidates = [self._cache_dir / f"{sym}.csv"]
        if sym.endswith(".HK"):
            code = sym.split(".")[0]
            candidates.append(self._cache_dir / f"{code}.csv")
            candidates.append(self._cache_dir / f"{code.zfill(5)}.HK.csv")
            candidates.append(self._cache_dir / f"{code.lstrip('0')}.HK.csv")
        for path in candidates:
            if path.exists() and path.stat().st_size > 50:
                return path
        return None
