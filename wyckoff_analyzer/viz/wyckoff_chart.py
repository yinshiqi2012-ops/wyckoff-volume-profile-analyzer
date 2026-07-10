"""Matplotlib composite Wyckoff + Volume Profile chart."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Union

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle

from wyckoff_analyzer.viz.plot_utils import (
    HVN_COLOR,
    LVN_COLOR,
    PHASE_COLORS,
    PHASE_FACE_ALPHA,
    POC_COLOR,
    VA_COLOR,
)


def _configure_chinese_font() -> None:
    """Prefer a Windows CJK font so stock names render on charts."""
    candidates = [
        "Microsoft YaHei",
        "SimHei",
        "PingFang SC",
        "Noto Sans CJK SC",
        "Arial Unicode MS",
    ]
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            plt.rcParams["font.sans-serif"] = [name, "DejaVu Sans"]
            plt.rcParams["axes.unicode_minus"] = False
            return


_configure_chinese_font()


def _to_plot_dates(dates: pd.Series) -> np.ndarray:
    parsed = pd.to_datetime(dates.astype(str), format="%Y%m%d", errors="coerce")
    if parsed.isna().all():
        parsed = pd.to_datetime(dates, errors="coerce")
    return mdates.date2num(parsed.dt.to_pydatetime())


def _draw_bars(ax, x, opens, highs, lows, closes):
    """Draw OHLCV bars (A-share colors: red up, green down)."""
    width = 0.6
    for i in range(len(x)):
        o, h, l, c = opens[i], highs[i], lows[i], closes[i]
        color = "#d32f2f" if c >= o else "#388e3c"
        ax.vlines(x[i], l, h, color=color, linewidth=0.8)
        lower = min(o, c)
        height = abs(c - o) or (h - l) * 0.02 or 0.01
        ax.add_patch(
            Rectangle(
                (x[i] - width / 2, lower),
                width,
                height,
                facecolor=color,
                edgecolor=color,
                linewidth=0.6,
            )
        )


def render_wyckoff_chart(
    result: Dict[str, Any],
    output_path: Union[str, Path],
    title: Optional[str] = None,
) -> Path:
    """Render K-line + VP histogram + volume/phase panel to PNG."""
    df: pd.DataFrame = result["_df"]
    vp = result["_vp"]
    phase = result["_phase"]

    x = np.arange(len(df))
    opens = df["open"].to_numpy(float)
    highs = df["high"].to_numpy(float)
    lows = df["low"].to_numpy(float)
    closes = df["close"].to_numpy(float)
    volumes = df["volume"].to_numpy(float)

    fig = plt.figure(figsize=(14, 9), constrained_layout=True)
    gs = fig.add_gridspec(3, 2, width_ratios=[4, 1.2], height_ratios=[3, 1.2, 0.05], hspace=0.05)
    ax_price = fig.add_subplot(gs[0, 0])
    ax_vp = fig.add_subplot(gs[0, 1], sharey=ax_price)
    ax_vol = fig.add_subplot(gs[1, 0], sharex=ax_price)
    ax_legend = fig.add_subplot(gs[2, :])
    ax_legend.axis("off")

    # Phase background as a time-band behind bars (not a price band)
    color = PHASE_COLORS.get(phase.phase, PHASE_COLORS["CONSOLIDATION"])
    alpha = PHASE_FACE_ALPHA.get(phase.phase, 0.12)
    ax_price.axvspan(x[0] - 0.5, x[-1] + 0.5, facecolor=color, alpha=alpha, zorder=0)

    _draw_bars(ax_price, x, opens, highs, lows, closes)

    # VP levels
    ax_price.axhline(vp.poc, color=POC_COLOR, linestyle="--", linewidth=1.2, label="POC")
    ax_price.axhline(vp.vah, color="#1565c0", linestyle=":", linewidth=1.0, label="VAH")
    ax_price.axhline(vp.val, color="#1565c0", linestyle=":", linewidth=1.0, label="VAL")
    ax_price.axhspan(vp.val, vp.vah, facecolor=VA_COLOR, alpha=0.15, zorder=0)

    # Events
    for ev in phase.events:
        if ev.index < 0 or ev.index >= len(x):
            continue
        if ev.kind == "SPRING":
            ax_price.annotate(
                "Spring",
                xy=(x[ev.index], ev.price),
                xytext=(0, -18),
                textcoords="offset points",
                color="#2e7d32",
                fontsize=8,
                ha="center",
                arrowprops=dict(arrowstyle="->", color="#2e7d32"),
            )
        elif ev.kind == "UPTHRUST":
            ax_price.annotate(
                "UT",
                xy=(x[ev.index], ev.price),
                xytext=(0, 14),
                textcoords="offset points",
                color="#c62828",
                fontsize=8,
                ha="center",
                arrowprops=dict(arrowstyle="->", color="#c62828"),
            )
        elif ev.kind in {"SOS", "SOW"}:
            marker = "*" if ev.kind == "SOS" else "X"
            color_m = "#2e7d32" if ev.kind == "SOS" else "#c62828"
            ax_price.scatter([x[ev.index]], [ev.price], marker=marker, s=60, color=color_m, zorder=5)

    sym = result.get("symbol") or ""
    name = (result.get("name") or "").strip()
    label = f"{name} {sym}" if name else sym
    phase_name = result.get("current_phase", "")
    conf = result.get("phase_confidence", 0)
    ax_price.set_title(
        title
        or f"{label}  |  {phase_name} ({conf:.0%})  |  POC={vp.poc:.2f} VA=[{vp.val:.2f},{vp.vah:.2f}]"
    )
    ax_price.set_ylabel("Price")
    ax_price.grid(True, alpha=0.25)
    ax_price.legend(loc="upper left", fontsize=8)

    # Volume profile histogram (horizontal)
    prices = np.array(sorted(vp.profile.keys()))
    vols = np.array([vp.profile[p] for p in prices])
    max_v = vols.max() if len(vols) else 1.0
    colors = []
    for p in prices:
        if p in vp.hvn:
            colors.append(HVN_COLOR)
        elif p in vp.lvn:
            colors.append(LVN_COLOR)
        else:
            colors.append("#90a4ae")
    ax_vp.barh(prices, vols, height=vp.bin_size * 0.9, color=colors, alpha=0.85)
    ax_vp.axhline(vp.poc, color=POC_COLOR, linestyle="--", linewidth=1.0)
    ax_vp.axhspan(vp.val, vp.vah, facecolor=VA_COLOR, alpha=0.2)
    ax_vp.set_xlabel("Volume")
    ax_vp.set_title("Volume Profile")
    ax_vp.grid(True, alpha=0.2)
    ax_vp.set_xlim(0, max_v * 1.05)

    # Volume bars + phase score line
    vol_colors = ["#d32f2f" if closes[i] >= opens[i] else "#388e3c" for i in range(len(x))]
    ax_vol.bar(x, volumes, color=vol_colors, width=0.6, alpha=0.8)
    ax_vol.set_ylabel("Volume")
    ax2 = ax_vol.twinx()
    ax2.plot(x, [phase.score] * len(x), color="#6a1b9a", linewidth=1.2, label="phase score")
    ax2.set_ylabel("Phase")
    ax2.set_ylim(-2.5, 2.5)
    ax_vol.grid(True, alpha=0.25)

    # X tick labels from dates
    step = max(len(df) // 8, 1)
    tick_idx = list(range(0, len(df), step))
    ax_vol.set_xticks(tick_idx)
    ax_vol.set_xticklabels([str(df["date"].iloc[i]) for i in tick_idx], rotation=30, ha="right")

    signals = result.get("signals") or []
    sig_txt = ", ".join(f"{s['type']}({s['confidence']:.2f})" for s in signals[:3])
    ax_legend.text(
        0.0,
        0.4,
        f"Signals: {sig_txt}   |   Source: {result.get('data_source') or 'n/a'}   |   "
        f"Disclaimer: analysis reference only, not investment advice.",
        fontsize=8,
        transform=ax_legend.transAxes,
    )

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return out
