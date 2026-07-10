"""Local CSV feed for cached OHLCV files."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import pandas as pd

from wyckoff_analyzer.data.base_feed import BaseFeed, normalize_ohlcv


class CsvFeed(BaseFeed):
    """Read OHLCV from a local CSV (columns date/open/high/low/close/volume)."""

    def __init__(self, path: Union[str, Path]):
        self.path = Path(path)

    def fetch(
        self,
        symbol: str,
        count: Optional[int] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        df = pd.read_csv(self.path)
        out = normalize_ohlcv(df)
        if start:
            out = out[out["date"] >= start.replace("-", "")]
        if end:
            out = out[out["date"] <= end.replace("-", "")]
        if count:
            out = out.tail(count)
        return out.reset_index(drop=True)
