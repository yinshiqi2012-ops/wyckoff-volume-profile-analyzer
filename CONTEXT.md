# Wyckoff Volume Profile Analyzer

A-share daily analysis tool that combines Volume Profile key levels with Wyckoff phase/event detection to produce structured trade signals.

## Language

### Market Data

**AnalysisWindow**:
The most recent N trading bars used to compute Volume Profile (default 60).
_Avoid_: lookback, period, sample

**Bar**:
One OHLCV daily candle with date, open, high, low, close, volume.
_Avoid_: candle, kline (in code), row

**ForwardAdjustedPrice**:
Price series adjusted for dividends and splits so historical levels align with the current market price (前复权).
_Avoid_: raw price, backward-adjusted

### Volume Profile

**POC (Point of Control)**:
The price level with the highest traded volume inside the AnalysisWindow.

**ValueArea**:
The contiguous price band around the POC that contains 70% of window volume, built by expanding outward from the POC.
_Avoid_: top-volume bins, VA nodes (scattered)

**VAH / VAL**:
The upper / lower boundary of the ValueArea.

**HVN (High Volume Node)**:
A price bin whose volume is significantly higher than its local neighbors.
_Avoid_: volume cluster (unless referring to adjacent HVNs as a group)

**LVN (Low Volume Node)**:
A price bin whose volume is significantly lower than its local neighbors.

**VolumeAllocation**:
A strategy that maps a single Bar's volume onto price bins (default: uniform across high–low).
_Avoid_: volume distribution (ambiguous with Volume Profile itself)

### Wyckoff

**WyckoffPhase**:
One of Accumulation, Markup, Distribution, or Markdown for the current AnalysisWindow. When structure is unclear, the engine may report Consolidation as a neutral holding state (not a classic Wyckoff schematic phase).
_Avoid_: trend, regime, stage (in code)

**Spring**:
A brief break below support that recovers within 3 bars, with depth ≤ 2% and non-expanding volume — a bullish trap / shakeout.

**Upthrust**:
A brief break above resistance that fails within 3 bars — the bearish counterpart of a Spring.

### Signals

**Signal**:
A structured advisory outcome: STRONG_BUY, BUY, STRONG_SELL, SELL, or WATCH, with confidence, entry, stop_loss, and targets.
_Avoid_: recommendation, alert (MVP has no alert system)

**KeyLevel**:
A support or resistance price derived from POC, VAH/VAL, HVN/LVN, or Spring/Upthrust extremes.
