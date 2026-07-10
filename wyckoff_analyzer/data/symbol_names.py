"""Resolve stock display names from warehouse / Tushare."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional


# Well-known overrides (esp. HK names not in A-share warehouse)
KNOWN_NAMES = {
    "09992.HK": "泡泡玛特",
    "9992.HK": "泡泡玛特",
    "03696.HK": "英矽智能",
    "3696.HK": "英矽智能",
}


def normalize_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if s.isdigit() and len(s) <= 5:
        # bare HK-style numeric → leave to caller; A-share usually 6 digits
        return s
    return s


def resolve_name(symbol: str, token: Optional[str] = None) -> str:
    """Return Chinese short name for a symbol, or empty string if unknown."""
    sym = normalize_symbol(symbol)
    if sym in KNOWN_NAMES:
        return KNOWN_NAMES[sym]

    # A-share warehouse stock_basic
    try:
        root = Path(r"D:\vibecoding")
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from data_warehouse import WarehouseClient

        wh = WarehouseClient()
        for row in wh._load_stock_basic():
            if row.get("symbol") == sym or row.get("ts_code") == sym:
                return str(row.get("name") or "")
            # pure numeric match
            code = sym.split(".")[0]
            if row.get("symbol", "").startswith(code) or row.get("ts_code", "").startswith(code):
                if row.get("ts_code") == sym or row.get("symbol") == code:
                    return str(row.get("name") or "")
    except Exception:
        pass

    # Tushare HK / A-share basic
    try:
        import tushare as ts
        from wyckoff_analyzer.data.tushare_feed import _load_token

        tok = token or _load_token()
        ts.set_token(tok)
        pro = ts.pro_api()
        if sym.endswith(".HK"):
            df = pro.hk_basic(ts_code=sym)
            if df is not None and not df.empty:
                return str(df.iloc[0]["name"])
        else:
            df = pro.stock_basic(ts_code=sym, fields="ts_code,name")
            if df is not None and not df.empty:
                return str(df.iloc[0]["name"])
    except Exception:
        pass

    return ""
