"""HTML analysis report with plain-language interpretation."""

from __future__ import annotations

import base64
import html
from pathlib import Path
from typing import Any, Dict, Optional, Union

from wyckoff_analyzer.viz.report_narrative import build_narrative


def _esc(s: Any) -> str:
    return html.escape("" if s is None else str(s))


def _img_data_uri(png_path: Path) -> str:
    data = png_path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _list_prices(items) -> str:
    if not items:
        return "<span class='muted'>无</span>"
    return "、".join(f"<code>{_esc(x)}</code>" for x in items)


def render_html_report(
    result: Dict[str, Any],
    chart_path: Union[str, Path],
    output_path: Union[str, Path],
) -> Path:
    """Write a self-contained HTML report (chart embedded) for browser / print-to-PDF."""
    chart_path = Path(chart_path)
    output_path = Path(output_path)
    narrative = build_narrative(result)
    img_uri = _img_data_uri(chart_path) if chart_path.exists() else ""

    events_html = ""
    if narrative["events"]:
        rows = "".join(
            f"<tr><td>{_esc(e['label'])}</td><td><code>{_esc(e['price'])}</code></td>"
            f"<td>{_esc(e['detail'])}</td></tr>"
            for e in narrative["events"]
        )
        events_html = f"""
        <table>
          <thead><tr><th>事件</th><th>价格</th><th>说明</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
        """
    else:
        events_html = "<p class='muted'>本窗口未检测到 Spring / Upthrust / SOS / SOW。没有事件不等于没有方向，请结合阶段与价值区位置理解。</p>"

    signals_html = ""
    for s in narrative["signals"]:
        signals_html += f"""
        <div class="card signal">
          <div class="signal-head">
            <strong>{_esc(s['type_zh'])}</strong>
            <span class="badge">{_esc(s['type'])}</span>
            <span class="conf">置信度 {_esc(s['confidence'])}</span>
          </div>
          <p class="trigger">触发条件：{_esc(s['trigger'])}</p>
          <div class="grid4">
            <div><span class="label">参考入场</span><code>{_esc(s['entry'])}</code></div>
            <div><span class="label">止损参考</span><code>{_esc(s['stop_loss'])}</code></div>
            <div><span class="label">目标1</span><code>{_esc(s['target_1'])}</code></div>
            <div><span class="label">目标2</span><code>{_esc(s['target_2'])}</code></div>
          </div>
        </div>
        """

    how_html = "".join(f"<li>{_esc(x)}</li>" for x in narrative["how_to_use"])
    glossary_html = "".join(
        f"<tr><th>{_esc(g['term'])}</th><td>{_esc(g['meaning'])}</td></tr>"
        for g in narrative["glossary"]
    )

    chart_block = (
        f'<img class="chart" src="{img_uri}" alt="Wyckoff chart"/>'
        if img_uri
        else "<p class='muted'>图表文件缺失</p>"
    )

    doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{_esc(narrative['title'])}</title>
  <style>
    :root {{
      --bg: #f7f4ef;
      --ink: #1c1917;
      --muted: #78716c;
      --card: #fffdf8;
      --line: #e7e0d5;
      --accent: #0f766e;
      --warn: #b45309;
      --bear: #b91c1c;
      --bull: #15803d;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(1200px 600px at 10% -10%, #e8f5f2 0%, transparent 55%),
        radial-gradient(900px 500px at 100% 0%, #f3e8d8 0%, transparent 50%),
        var(--bg);
      line-height: 1.65;
    }}
    .wrap {{ max-width: 980px; margin: 0 auto; padding: 32px 20px 64px; }}
    header {{
      border-bottom: 1px solid var(--line);
      padding-bottom: 18px;
      margin-bottom: 24px;
    }}
    h1 {{
      margin: 0 0 6px;
      font-size: 1.85rem;
      letter-spacing: 0.02em;
    }}
    .subtitle {{ color: var(--muted); margin: 0; }}
    .meta {{
      display: flex; flex-wrap: wrap; gap: 10px; margin-top: 14px;
    }}
    .pill {{
      background: #ecfdf5; color: var(--accent);
      border: 1px solid #99f6e4; border-radius: 999px;
      padding: 4px 12px; font-size: 0.85rem;
    }}
    h2 {{
      margin: 28px 0 12px;
      font-size: 1.2rem;
      border-left: 4px solid var(--accent);
      padding-left: 10px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 16px 18px;
      margin: 12px 0;
    }}
    .grid2 {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }}
    .grid4 {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
    }}
    .label {{ display: block; color: var(--muted); font-size: 0.8rem; }}
    code {{
      font-family: ui-monospace, Consolas, monospace;
      background: #f5f0e8;
      padding: 1px 6px;
      border-radius: 4px;
    }}
    .muted {{ color: var(--muted); }}
    .chart {{
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 10px;
      background: white;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--card);
    }}
    th, td {{
      border: 1px solid var(--line);
      padding: 8px 10px;
      text-align: left;
      vertical-align: top;
    }}
    th {{ background: #f3eee5; width: 28%; }}
    .signal-head {{ display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }}
    .badge {{
      background: #fff7ed; color: var(--warn);
      border: 1px solid #fed7aa; border-radius: 6px;
      padding: 2px 8px; font-size: 0.8rem;
    }}
    .conf {{ color: var(--muted); font-size: 0.9rem; }}
    .trigger {{ margin: 8px 0 12px; }}
    ol {{ padding-left: 1.2rem; }}
    li {{ margin: 6px 0; }}
    footer {{
      margin-top: 28px;
      padding-top: 14px;
      border-top: 1px solid var(--line);
      color: var(--muted);
      font-size: 0.9rem;
    }}
    .actions {{
      margin: 12px 0 0;
      display: flex; gap: 10px; flex-wrap: wrap;
    }}
    .btn {{
      appearance: none; border: 1px solid var(--accent); background: var(--accent);
      color: white; border-radius: 8px; padding: 8px 14px; cursor: pointer;
      font-size: 0.9rem;
    }}
    .btn.secondary {{ background: transparent; color: var(--accent); }}
    @media (max-width: 720px) {{
      .grid2, .grid4 {{ grid-template-columns: 1fr 1fr; }}
    }}
    @media print {{
      body {{ background: white; }}
      .actions {{ display: none; }}
      .wrap {{ max-width: none; padding: 0; }}
      .card, .chart {{ break-inside: avoid; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <h1>{_esc(narrative['title'])}</h1>
      <p class="subtitle">{_esc(narrative['subtitle'])}</p>
      <div class="meta">
        <span class="pill">股票：{_esc(narrative.get('display_name') or narrative.get('symbol') or '')}</span>
        <span class="pill">阶段：{_esc(narrative['phase_zh'])}（{_esc(narrative['phase_confidence_pct'])}）</span>
        <span class="pill">最新收盘：{_esc(narrative['last_close'])}</span>
        <span class="pill">数据源：{_esc(narrative['data_source'])}</span>
      </div>
      <div class="actions">
        <button class="btn" onclick="window.print()">打印 / 另存为 PDF</button>
        <button class="btn secondary" onclick="window.scrollTo({{top: document.body.scrollHeight, behavior: 'smooth'}})">看术语表</button>
      </div>
    </header>

    <h2>一句话结论</h2>
    <div class="card">
      <p>
        当前判断为<strong>{_esc(narrative['phase_zh'])}</strong>
        （{_esc(narrative['phase_code'])}，置信度 {_esc(narrative['phase_confidence_pct'])}）。
        {_esc(narrative['phase_explain'])}
      </p>
      <p>
        最新收盘 <code>{_esc(narrative['last_close'])}</code>，相对价值区位置：
        <strong>{_esc(narrative['price_position'])}</strong>。
        {_esc(narrative['price_position_tip'])}
      </p>
    </div>

    <h2>图表怎么看</h2>
    <div class="card">
      {chart_block}
      <p class="muted" style="margin-top:12px">
        左图：K 线 + 阶段背景色 + POC/VAH/VAL 水平线。右图：成交量按价格分布（Volume Profile）。
        下图：每日成交量。金色虚线是 POC，蓝色点线是价值区上下沿。
      </p>
    </div>

    <h2>关键价位（Volume Profile）</h2>
    <div class="grid2">
      <div class="card">
        <div class="label">POC（成交最密集）</div>
        <div style="font-size:1.4rem"><code>{_esc(narrative['poc'])}</code></div>
        <p class="muted">价格常围绕这里来回；远离后回踩/反抽时值得关注。</p>
      </div>
      <div class="card">
        <div class="label">价值区 VA</div>
        <div>VAL <code>{_esc(narrative['val'])}</code> ~ VAH <code>{_esc(narrative['vah'])}</code></div>
        <p class="muted">约 70% 成交发生在这个价格带内。</p>
      </div>
    </div>
    <div class="card">
      <p><strong>强支撑：</strong>{_list_prices(narrative['strong_support'])}</p>
      <p><strong>中等支撑：</strong>{_list_prices(narrative['moderate_support'])}</p>
      <p><strong>中等阻力：</strong>{_list_prices(narrative['moderate_resistance'])}</p>
      <p><strong>强阻力：</strong>{_list_prices(narrative['strong_resistance'])}</p>
      <p><strong>HVN：</strong>{_list_prices(narrative['hvn'])}</p>
      <p><strong>LVN：</strong>{_list_prices(narrative['lvn'])}</p>
    </div>

    <h2>威科夫事件</h2>
    <div class="card">{events_html}</div>

    <h2>信号解读</h2>
    {signals_html}

    <h2>你可以怎么用这份报告</h2>
    <div class="card"><ol>{how_html}</ol></div>

    <h2 id="glossary">术语小词典</h2>
    <table>
      <tbody>{glossary_html}</tbody>
    </table>

    <footer>
      {_esc(narrative['disclaimer'])}<br/>
      提示：点击上方「打印 / 另存为 PDF」，在打印对话框中选择「另存为 PDF」即可导出 PDF。
    </footer>
  </div>
</body>
</html>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(doc, encoding="utf-8")
    return output_path
