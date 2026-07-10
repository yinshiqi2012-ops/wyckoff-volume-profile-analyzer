# ADR-0004: Local-peak HVN/LVN detection

## Status

Accepted

## Context

HVN/LVN need a quantitative definition of "significantly higher/lower than neighbors." Percentile ranking across the whole profile can mark entire regions as HVN without local structure.

## Decision

A bin is an HVN when its volume exceeds the mean of its left/right N neighbors by a multiplier (default N=2, multiplier=1.5). A bin is an LVN when its volume is below the neighbor mean by a low multiplier (default 0.5). Parameters are configurable.

## Consequences

- Nodes reflect local structure, matching the "node" intuition.
- Edge bins with fewer neighbors are skipped or use available neighbors only.
