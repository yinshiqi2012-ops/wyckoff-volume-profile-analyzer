"""Tests for report narrative and HTML generation."""

from __future__ import annotations

from pathlib import Path

from wyckoff_analyzer.viz.report_narrative import build_narrative
from wyckoff_analyzer.viz.html_report import render_html_report


def _sample_result():
    return {
        "symbol": "600519.SH",
        "name": "贵州茅台",
        "data_source": "warehouse",
        "window": 60,
        "current_phase": "MARKDOWN",
        "phase_confidence": 0.78,
        "recent_events": [],
        "volume_profile": {
            "poc": 1410.5,
            "vah": 1421.9,
            "val": 1245.7,
            "hvn": [1338.7],
            "lvn": [1394.2],
        },
        "signals": [
            {
                "type": "WATCH",
                "trigger": "Phase=MARKDOWN; no matrix match",
                "entry": 1199.3,
                "stop_loss": 1175.31,
                "target_1": 1421.92,
                "target_2": 1493.02,
                "confidence": 0.3,
            }
        ],
        "key_levels": {
            "strong_resistance": [1477.41, 1421.92],
            "moderate_resistance": [1420.29],
            "poc": 1410.5,
            "moderate_support": [1400.71],
            "strong_support": [1245.67, 1151.01],
        },
        "last_close": 1199.3,
        "date_range": {"start": "20260409", "end": "20260708"},
    }


def test_narrative_explains_markdown_below_val():
    n = build_narrative(_sample_result())
    assert n["phase_zh"] == "下跌"
    assert "下方" in n["price_position"]
    assert len(n["how_to_use"]) >= 4
    assert n["signals"][0]["type_zh"] == "观望"
    assert "贵州茅台" in n["title"]
    assert n["display_name"] == "贵州茅台（600519.SH）"


def test_html_report_written(tmp_path: Path):
    png = tmp_path / "x.png"
    # Tiny valid PNG payload is unnecessary; report only base64-embeds bytes.
    png.write_bytes(b"fake-png-bytes-for-embed")
    out = tmp_path / "x.html"
    path = render_html_report(_sample_result(), png, out)
    text = path.read_text(encoding="utf-8")
    assert "威科夫量价分析报告" in text
    assert "600519.SH" in text
    assert "一句话结论" in text
    assert "data:image/png;base64," in text
    assert "打印 / 另存为 PDF" in text
    assert "下跌" in text
