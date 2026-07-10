# 威科夫量价分析器（Wyckoff Volume Profile Analyzer）

A 股日线 MVP：用 **Volume Profile** 找关键价位，用 **威科夫阶段/事件** 判断结构，输出结构化信号与图表。

> **免责声明**：本工具仅供学习与研究参考，不构成投资建议。

## 功能（MVP）

- Volume Profile：POC、Value Area（从 POC 向外扩展至 70%）、HVN/LVN
- 威科夫：四阶段识别 + Spring / Upthrust（严格规则）
- 信号矩阵：STRONG_BUY / BUY / STRONG_SELL / SELL / WATCH
- 数据：本地 DuckDB / `data_warehouse` 优先，缺失时 fallback 到 Tushare 前复权
- 输出：`output/{symbol}.png` + `output/{symbol}.json` + **`output/{symbol}.html` 解读报告**（可浏览器打印为 PDF）

## 安装

```bash
cd "D:\vibecoding\Wyckoff Volume Profile Analyzer"
pip install -r requirements.txt
```

可选：复制 `.env.example` 为 `.env`，填入 `TUSHARE_TOKEN`（仅在本地仓库缺数据时需要）。

本地数据默认读取 `D:\vibecoding\data_warehouse`（DuckDB：`daily/stock/stock_warehouse.duckdb`）。

## 使用

```bash
python examples/analyze_single.py 600519.SH
python examples/analyze_single.py 000001.SZ --window 60
python examples/analyze_single.py 600519.SH --no-tushare-fallback
```

分析完成后打开 `output/600519.SH.html`：里面有白话结论、图表解读、关键价位、信号用法和术语表。需要 PDF 时，在浏览器里点「打印 / 另存为 PDF」即可。

## 库调用

```python
from wyckoff_analyzer.analyzer import WyckoffAnalyzer

analyzer = WyckoffAnalyzer.from_symbol("600519.SH", window=60)
result = analyzer.analyze()
print(result["current_phase"], result["signals"])
```

## 测试

```bash
python -m pytest -v
```

## 领域文档

- [CONTEXT.md](CONTEXT.md) — 术语表
- [docs/adr/](docs/adr/) — 架构决策记录
