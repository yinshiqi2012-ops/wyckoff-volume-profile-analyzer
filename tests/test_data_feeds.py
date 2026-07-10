"""Tests for data normalization and composite feed behavior."""

from __future__ import annotations

import pandas as pd

from wyckoff_analyzer.data.base_feed import normalize_ohlcv
from wyckoff_analyzer.data.composite_feed import CompositeFeed
from wyckoff_analyzer.data.base_feed import BaseFeed


class _FakeFeed(BaseFeed):
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.calls = 0

    def fetch(self, symbol, count=None, start=None, end=None):
        self.calls += 1
        return self.df


def test_normalize_renames_trade_date_and_vol():
    raw = pd.DataFrame(
        [
            {
                "trade_date": "20260102",
                "open": 10,
                "high": 11,
                "low": 9,
                "close": 10.5,
                "vol": 1000,
            }
        ]
    )
    out = normalize_ohlcv(raw)
    assert list(out.columns) == ["date", "open", "high", "low", "close", "volume"]
    assert out.iloc[0]["volume"] == 1000


def test_composite_uses_warehouse_when_present():
    wh_df = pd.DataFrame(
        [
            {
                "date": "20260101",
                "open": 1,
                "high": 2,
                "low": 1,
                "close": 1.5,
                "volume": 10,
            }
        ]
    )
    ts_df = pd.DataFrame(
        [
            {
                "date": "20260102",
                "open": 9,
                "high": 9,
                "low": 9,
                "close": 9,
                "volume": 1,
            }
        ]
    )
    wh = _FakeFeed(wh_df)
    ts = _FakeFeed(ts_df)
    feed = CompositeFeed(warehouse=wh, tushare=ts)
    out = feed.fetch("600519.SH", count=1)
    assert feed.last_source == "warehouse"
    assert out.iloc[0]["close"] == 1.5
    assert ts.calls == 0


def test_composite_falls_back_to_tushare_when_warehouse_empty():
    wh = _FakeFeed(pd.DataFrame())
    ts_df = pd.DataFrame(
        [
            {
                "date": "20260102",
                "open": 9,
                "high": 10,
                "low": 8,
                "close": 9.5,
                "volume": 100,
            }
        ]
    )
    ts = _FakeFeed(ts_df)
    feed = CompositeFeed(warehouse=wh, tushare=ts)
    out = feed.fetch("999999.SH", count=1)
    assert feed.last_source == "tushare"
    assert out.iloc[0]["close"] == 9.5
