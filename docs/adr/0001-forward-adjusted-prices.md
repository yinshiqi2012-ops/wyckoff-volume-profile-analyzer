# ADR-0001: Forward-adjusted prices as the A-share analysis baseline

## Status

Accepted

## Context

A-share dividends and splits create artificial gaps in unadjusted OHLCV. Those gaps pollute POC, ValueArea, and support/resistance derived from Volume Profile.

## Decision

All analysis uses forward-adjusted (前复权) daily bars. Local warehouse data is already stored as `adj="qfq"`. Tushare fallback also requests `adj="qfq"`.

## Consequences

- Current market price stays the anchor; historical levels remain comparable.
- Absolute historical prices differ from exchange-printed prints on ex-dividend days — this is intentional for technical analysis.
