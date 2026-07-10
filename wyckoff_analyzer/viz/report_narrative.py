"""Build plain-language narrative for an analysis result."""

from __future__ import annotations

from typing import Any, Dict, List


PHASE_ZH = {
    "ACCUMULATION": "吸筹",
    "MARKUP": "拉升",
    "DISTRIBUTION": "派发",
    "MARKDOWN": "下跌",
    "CONSOLIDATION": "震荡整理",
}

PHASE_EXPLAIN = {
    "ACCUMULATION": "价格多在区间内震荡，量能偏弱，可能有资金在低位慢慢买入。",
    "MARKUP": "价格已离开吸筹区向上推进，结构偏多，回调时更关注支撑是否守住。",
    "DISTRIBUTION": "价格在高位区间震荡，上涨乏力或放量滞涨，可能有资金在高位卖出。",
    "MARKDOWN": "价格已跌破关键支撑/价值区下沿，结构偏空，反弹时更关注阻力是否压住。",
    "CONSOLIDATION": "多空暂时平衡，没有清晰的威科夫阶段特征，宜观望等待事件确认。",
}

SIGNAL_ZH = {
    "STRONG_BUY": "强买入参考",
    "BUY": "买入参考",
    "STRONG_SELL": "强卖出参考",
    "SELL": "卖出参考",
    "WATCH": "观望",
}

EVENT_ZH = {
    "SPRING": "弹簧（假跌破后快速收回）",
    "UPTHRUST": "向上假突破（冲高后快速回落）",
    "SOS": "强势信号（放量向上突破）",
    "SOW": "弱势信号（放量向下跌破）",
}


def _fmt_date(s: str) -> str:
    s = str(s).replace("-", "")
    if len(s) == 8 and s.isdigit():
        return f"{s[:4]}-{s[4:6]}-{s[6:]}"
    return s


def _fmt_price(x: Any) -> str:
    try:
        return f"{float(x):.2f}"
    except (TypeError, ValueError):
        return str(x)


def build_narrative(result: Dict[str, Any]) -> Dict[str, Any]:
    """Return structured Chinese narrative sections for HTML/PDF report."""
    phase = result.get("current_phase", "CONSOLIDATION")
    conf = float(result.get("phase_confidence") or 0)
    vp = result.get("volume_profile") or {}
    close = result.get("last_close")
    levels = result.get("key_levels") or {}
    signals = result.get("signals") or []
    events = result.get("recent_events") or []
    date_range = result.get("date_range") or {}

    poc = vp.get("poc")
    vah = vp.get("vah")
    val = vp.get("val")

    position = "价值区内部"
    position_tip = "价格在多数成交发生的区间内，方向往往不清晰，适合等待突破或事件。"
    if close is not None and val is not None and vah is not None:
        if close < val:
            position = "价值区下方（偏弱）"
            position_tip = "收盘价已低于 VAL，说明市场暂时不认可原先的价值区，偏空解读更常见。"
        elif close > vah:
            position = "价值区上方（偏强）"
            position_tip = "收盘价已高于 VAH，说明买盘愿意在更高价成交，偏多解读更常见。"

    primary = signals[0] if signals else None
    signal_type = primary.get("type") if primary else "WATCH"

    how_to_use: List[str] = [
        "先看「当前阶段」和「价格相对价值区位置」，判断大方向偏多、偏空还是观望。",
        "再看 POC / VAH / VAL：它们是筹码最集中的参考价位，不是保证会反弹/受阻的铁律。",
        "若出现 Spring / Upthrust，优先结合信号矩阵里的入场、止损、目标价理解，而不是只看箭头。",
        "信号置信度低于 0.5 时，默认当作「观察清单」，不要当成交易指令。",
        "本报告仅供学习研究，不构成投资建议；实盘请结合自身风控与更多信息。",
    ]

    if signal_type in {"STRONG_BUY", "BUY"}:
        how_to_use.insert(
            3,
            f"若参考偏多信号：关注入场附近 {_fmt_price(primary.get('entry'))}，"
            f"止损参考 {_fmt_price(primary.get('stop_loss'))}，"
            f"目标参考 {_fmt_price(primary.get('target_1'))} / {_fmt_price(primary.get('target_2'))}。",
        )
    elif signal_type in {"STRONG_SELL", "SELL"}:
        how_to_use.insert(
            3,
            f"若参考偏空信号：关注入场附近 {_fmt_price(primary.get('entry'))}，"
            f"止损参考 {_fmt_price(primary.get('stop_loss'))}，"
            f"目标参考 {_fmt_price(primary.get('target_1'))} / {_fmt_price(primary.get('target_2'))}。",
        )
    elif phase == "MARKDOWN":
        how_to_use.insert(
            3,
            "当前偏下跌结构：反弹到 POC 或 VAH 附近时，更适合观察是否受阻，而不是急于抄底。",
        )
    elif phase == "MARKUP":
        how_to_use.insert(
            3,
            "当前偏拉升结构：回调到 POC 或 VAL 附近时，更适合观察是否获得支撑。",
        )

    event_lines = []
    for e in events:
        kind = e.get("kind", "")
        event_lines.append(
            {
                "kind": kind,
                "label": EVENT_ZH.get(kind, kind),
                "price": _fmt_price(e.get("price")),
                "detail": e.get("detail") or "",
            }
        )

    symbol = result.get("symbol") or ""
    name = (result.get("name") or "").strip()
    display = f"{name}（{symbol}）" if name else symbol

    return {
        "title": f"{display} 威科夫量价分析报告",
        "display_name": display,
        "name": name,
        "symbol": symbol,
        "subtitle": (
            f"分析窗口 {_fmt_date(date_range.get('start', ''))} ~ "
            f"{_fmt_date(date_range.get('end', ''))}（最近 {result.get('window', 60)} 个交易日）"
        ),
        "phase_zh": PHASE_ZH.get(phase, phase),
        "phase_code": phase,
        "phase_confidence_pct": f"{conf:.0%}",
        "phase_explain": PHASE_EXPLAIN.get(phase, ""),
        "price_position": position,
        "price_position_tip": position_tip,
        "last_close": _fmt_price(close),
        "poc": _fmt_price(poc),
        "vah": _fmt_price(vah),
        "val": _fmt_price(val),
        "hvn": [_fmt_price(x) for x in (vp.get("hvn") or [])[:8]],
        "lvn": [_fmt_price(x) for x in (vp.get("lvn") or [])[:8]],
        "strong_support": [_fmt_price(x) for x in (levels.get("strong_support") or [])],
        "strong_resistance": [_fmt_price(x) for x in (levels.get("strong_resistance") or [])],
        "moderate_support": [_fmt_price(x) for x in (levels.get("moderate_support") or [])],
        "moderate_resistance": [_fmt_price(x) for x in (levels.get("moderate_resistance") or [])],
        "events": event_lines,
        "signals": [
            {
                "type": s.get("type"),
                "type_zh": SIGNAL_ZH.get(s.get("type"), s.get("type")),
                "trigger": s.get("trigger"),
                "entry": _fmt_price(s.get("entry")),
                "stop_loss": _fmt_price(s.get("stop_loss")),
                "target_1": _fmt_price(s.get("target_1")),
                "target_2": _fmt_price(s.get("target_2")),
                "confidence": f"{float(s.get('confidence') or 0):.0%}",
            }
            for s in signals
        ],
        "how_to_use": how_to_use,
        "glossary": [
            {"term": "POC", "meaning": "成交量最大的价格，常被视为多空暂时平衡的「中枢价」。"},
            {"term": "VA / VAH / VAL", "meaning": "约 70% 成交发生的价格带，及其上沿/下沿。"},
            {"term": "HVN", "meaning": "高成交量节点，价格到这里容易减速、停留或反转。"},
            {"term": "LVN", "meaning": "低成交量节点，价格穿过这里往往更快、阻力更小。"},
            {"term": "Spring", "meaning": "短暂跌破支撑又迅速收回，常被解读为震仓后的看涨试探。"},
            {"term": "Upthrust", "meaning": "短暂突破阻力又迅速回落，常被解读为诱多后的看跌试探。"},
        ],
        "data_source": result.get("data_source") or "n/a",
        "disclaimer": "本报告仅供学习与研究参考，不构成任何投资建议或买卖依据。",
    }
