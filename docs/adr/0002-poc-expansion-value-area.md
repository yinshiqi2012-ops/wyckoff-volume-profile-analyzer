# ADR-0002: Value Area via POC expansion

## Status

Accepted

## Context

The original project prompt computed Value Area by taking the highest-volume bins until 70% of volume was reached. That can produce a non-contiguous set of prices, which breaks the meaning of VAH/VAL as band edges.

## Decision

Build Value Area by starting at the POC and alternately expanding to the adjacent higher/lower bin with more volume until cumulative volume reaches 70% of the AnalysisWindow total.

## Consequences

- VA is always a contiguous price band.
- Aligns with common Volume Profile tooling (e.g. TradingView-style VA).
- Differs from the prompt's top-bins pseudocode — intentional.
