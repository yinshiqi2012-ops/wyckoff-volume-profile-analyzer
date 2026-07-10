# ADR-0003: Pluggable VolumeAllocation with uniform default

## Status

Accepted

## Context

Bar volume must be mapped onto price bins. Uniform allocation across high–low is simple and explainable but slightly flattens peaks. Close-weighted allocation is more realistic but adds complexity.

## Decision

Expose a `VolumeAllocation` strategy interface. MVP ships `UniformAllocation` as the default. Close-weighted (or other) strategies can be added later without changing the Volume Profile public API.

## Consequences

- MVP stays simple and testable.
- Callers can inject an alternate strategy in Phase 2 without rewriting the engine.
