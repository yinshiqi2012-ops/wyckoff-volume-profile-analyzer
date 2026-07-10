"""yfinance feed for HK (and other) symbols when warehouse/Tushare unavailable."""

from __future__ import annotations

from typing import Optional

import pandas as pd

from wyckoff_analyzer.data.base_feed import BaseFeed, normalize_ohlcv


def to_yahoo_symbol(symbol: str) -> str:
    """Map Tushare-style codes to Yahoo Finance tickers."""
    s = symbol.strip().upper()
    if s.endswith(".HK"):
        code = s.split(".")[0].lstrip("0") or "0"
        # Yahoo uses 4-digit HK codes without leading zeros beyond 4? Actually 9992.HK / 3696.HK
        return f"{code}.HK"
    if s.endswith(".SH"):
        return f"{s.split('.')[0]}.SS"
    if s.endswith(".SZ"):
        return f"{s.split('.')[0]}.SZ"
    return s


class YFinanceFeed(BaseFeed):
    """Secondary fallback using Yahoo Finance."""

    def fetch(
        self,
        symbol: str,
        count: Optional[int] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        import yfinance as yf

        ticker = to_yahoo_symbol(symbol)
        kwargs = {"interval": "1d", "auto_adjust": True, "progress": False}
        if start or end:
            kwargs["start"] = _to_iso(start) if start else None
            kwargs["end"] = _to_iso(end) if end else None
            raw = yf.download(ticker, **{k: v for k, v in kwargs.items() if v is not None})
        else:
            period = "1y" if not count or count > 120 else "6mo"
            raw = yf.download(ticker, period=period, **kwargs)

        if raw is None or raw.empty:
            return normalize_ohlcv(pd.DataFrame())

        # yfinance may return MultiIndex columns
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = [c[0] for c in raw.columns]

        out = raw.reset_index()
        date_col = "Date" if "Date" in out.columns else out.columns[0]
        out = out.rename(
            columns={
                date_col: "date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )
        out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y%m%d")
        out = normalize_ohlcv(out)
        if count:
            out = out.tail(count).reset_index(drop=True)
        return out


def _to_iso(d: str) -> str:
    d = d.replace("-", "")
    if len(d) == 8:
        return f"{d[:4]}-{d[4:6]}-{d[6:]}"
    return d
