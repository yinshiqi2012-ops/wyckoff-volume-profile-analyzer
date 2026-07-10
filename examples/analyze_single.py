#!/usr/bin/env python
"""CLI: analyze a single A-share symbol and write PNG + JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running as script from repo root / examples/
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wyckoff_analyzer.analyzer import WyckoffAnalyzer
from wyckoff_analyzer.viz.html_report import render_html_report
from wyckoff_analyzer.viz.wyckoff_chart import render_wyckoff_chart


def _json_safe(result: dict) -> dict:
    return {k: v for k, v in result.items() if not k.startswith("_")}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Wyckoff Volume Profile Analyzer (A-share daily MVP)"
    )
    parser.add_argument("symbol", help="Stock code, e.g. 600519.SH or 000001.SZ")
    parser.add_argument("--window", type=int, default=60, help="AnalysisWindow bars (default 60)")
    parser.add_argument("--bins", type=int, default=100, help="VP bin count (default 100)")
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "output"),
        help="Directory for PNG/JSON/HTML outputs",
    )
    parser.add_argument(
        "--no-tushare-fallback",
        action="store_true",
        help="Disable Tushare fallback (warehouse only)",
    )
    parser.add_argument(
        "--no-html",
        action="store_true",
        help="Skip HTML analysis report",
    )
    args = parser.parse_args(argv)

    from wyckoff_analyzer.data.composite_feed import CompositeFeed

    feed = CompositeFeed(enable_tushare_fallback=not args.no_tushare_fallback)
    analyzer = WyckoffAnalyzer.from_symbol(
        args.symbol,
        window=args.window,
        num_bins=args.bins,
        feed=feed,
    )
    result = analyzer.analyze()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = args.symbol.replace("/", "_")
    png_path = out_dir / f"{stem}.png"
    json_path = out_dir / f"{stem}.json"
    html_path = out_dir / f"{stem}.html"

    render_wyckoff_chart(result, png_path)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(_json_safe(result), f, ensure_ascii=False, indent=2)

    if not args.no_html:
        render_html_report(result, png_path, html_path)

    name = result.get("name") or ""
    print(f"symbol:     {result['symbol']}" + (f"  {name}" if name else ""))
    print(f"source:     {result.get('data_source')}")
    print(f"phase:      {result['current_phase']} ({result['phase_confidence']:.0%})")
    print(f"events:     {[e['kind'] for e in result['recent_events']]}")
    print(f"POC/VA:     {result['volume_profile']['poc']} / "
          f"[{result['volume_profile']['val']}, {result['volume_profile']['vah']}]")
    print(f"signals:    {[s['type'] for s in result['signals']]}")
    print(f"bars:       {result.get('bars')} (window={result.get('window')})")
    print(f"chart:      {png_path}")
    print(f"json:       {json_path}")
    if not args.no_html:
        print(f"html:       {html_path}")
        print("tip:        用浏览器打开 html，可点击「打印 / 另存为 PDF」导出 PDF")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
