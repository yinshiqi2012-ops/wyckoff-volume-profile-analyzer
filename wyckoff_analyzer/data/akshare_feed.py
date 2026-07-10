"""akshare feed for HK daily bars."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from wyckoff_analyzer.data.base_feed import BaseFeed, normalize_ohlcv


def _hk_code(symbol: str) -> str:
    s = symbol.strip().upper()
    if s.endswith(".HK"):
        return s.split(".")[0].zfill(5)
    return s.zfill(5)


class AkshareFeed(BaseFeed):
    """HK daily via akshare.stock_hk_hist (forward-adjusted when adjust=qfq)."""

    def fetch(
        self,
        symbol: str,
        count: Optional[int] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        import akshare as ak

        code = _hk_code(symbol)
        if not end:
            end = datetime.now().strftime("%Y%m%d")
        else:
            end = end.replace("-", "")
        if not start:
            days = (count or 120) * 2 + 30
            start = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        else:
            start = start.replace("-", "")

        df = ak.stock_hk_hist(
            symbol=code,
            period="daily",
            start_date=start,
            end_date=end,
            adjust="qfq",
        )
        if df is None or df.empty:
            return normalize_ohlcv(pd.DataFrame())

        rename = {
            "日期": "date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
        }
        out = df.rename(columns=rename)
        out = normalize_ohlcv(out)
        if count:
            out = out.tail(count).reset_index(drop=True)
        return out
