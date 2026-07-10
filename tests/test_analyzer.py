"""End-to-end analyzer tests with synthetic bars."""

from __future__ import annotations

import pandas as pd

from wyckoff_analyzer.analyzer import WyckoffAnalyzer


def _synth(n=60):
    rows = []
    price = 10.0
    for i in range(n):
        # mild range then slight up
        drift = 0.02 if i > 40 else 0.0
        price = price + drift
        rows.append(
            {
                "date": f"{20250101 + i}",
                "open": price,
                "high": price + 0.3,
                "low": price - 0.3,
                "close": price + 0.05,
                "volume": 100 + (i % 7) * 10,
            }
        )
    return pd.DataFrame(rows)


def test_analyzer_returns_required_report_fields():
    result = WyckoffAnalyzer(_synth(), symbol="TEST.SZ", window=60).analyze()
    assert result["symbol"] == "TEST.SZ"
    assert result["current_phase"] in {
        "ACCUMULATION",
        "MARKUP",
        "DISTRIBUTION",
        "MARKDOWN",
        "CONSOLIDATION",
    }
    assert "poc" in result["volume_profile"]
    assert "vah" in result["volume_profile"]
    assert "val" in result["volume_profile"]
    assert isinstance(result["signals"], list)
    assert len(result["signals"]) >= 1
    assert "key_levels" in result
    assert result["volume_profile"]["val"] <= result["volume_profile"]["poc"] <= result[
        "volume_profile"
    ]["vah"]
