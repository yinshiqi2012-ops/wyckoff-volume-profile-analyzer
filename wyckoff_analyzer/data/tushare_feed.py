"""Tushare Pro feed: A-share qfq via pro_bar; HK via hk_daily."""

from __future__ import annotations

import os
from typing import Optional

import pandas as pd

from wyckoff_analyzer.data.base_feed import BaseFeed, normalize_ohlcv


def _load_token() -> str:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    token = os.environ.get("TUSHARE_TOKEN", "").strip()
    if token:
        return token

    try:
        import sys
        from pathlib import Path

        root = Path(r"D:\vibecoding")
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from data_warehouse.config import TUSHARE_TOKEN as WH_TOKEN

        if WH_TOKEN:
            return str(WH_TOKEN)
    except Exception:
        pass

    raise RuntimeError(
        "TUSHARE_TOKEN not set. Add it to environment or .env for fallback fetches."
    )


def _is_hk(symbol: str) -> bool:
    return symbol.upper().endswith(".HK")


class TushareFeed(BaseFeed):
    """Fallback feed when local warehouse has no data."""

    def __init__(self, token: Optional[str] = None):
        self._token = token

    def fetch(
        self,
        symbol: str,
        count: Optional[int] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        import tushare as ts

        token = self._token or _load_token()
        ts.set_token(token)
        pro = ts.pro_api()
        symbol = symbol.strip().upper()

        if _is_hk(symbol):
            return self._fetch_hk(pro, symbol, count=count, start=start, end=end)

        kwargs = {"ts_code": symbol, "adj": "qfq", "asset": "E", "freq": "D"}
        if start:
            kwargs["start_date"] = start.replace("-", "")
        if end:
            kwargs["end_date"] = end.replace("-", "")

        # Always use pro_bar with adj=qfq — never fall back to unadjusted pro.daily
        df = ts.pro_bar(**kwargs)
        if df is None or df.empty:
            return normalize_ohlcv(pd.DataFrame())

        if count:
            df = df.sort_values("trade_date").tail(count)
        return normalize_ohlcv(df)

    def _fetch_hk(
        self,
        pro,
        symbol: str,
        count: Optional[int] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        kwargs = {"ts_code": symbol}
        if start:
            kwargs["start_date"] = start.replace("-", "")
        if end:
            kwargs["end_date"] = end.replace("-", "")
        df = pro.hk_daily(**kwargs)
        if df is None or df.empty:
            return normalize_ohlcv(pd.DataFrame())
        if count:
            df = df.sort_values("trade_date").tail(count)
        return normalize_ohlcv(df)
