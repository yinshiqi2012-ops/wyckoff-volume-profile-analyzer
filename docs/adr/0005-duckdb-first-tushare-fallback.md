# ADR-0005: DuckDB warehouse first, Tushare fallback

## Status

Accepted

## Context

The vibecoding workspace already maintains `data_warehouse` with forward-adjusted A-share daily bars in DuckDB (`stock_warehouse.duckdb`) and CSV. Re-fetching every analysis from Tushare is slower, rate-limited, and duplicates local data.

## Decision

Data loading order:

1. `WarehouseClient.daily()` (DuckDB stock layer, CSV fallback inside the client)
2. If missing/empty/error → Tushare Pro `pro_bar(..., adj="qfq")` using `TUSHARE_TOKEN` from environment / `.env`

Normalize all sources to columns: `date, open, high, low, close, volume`.

## Consequences

- Offline analysis works for symbols already in the warehouse.
- Tushare remains available for gaps or symbols not yet synced.
- This project depends on `D:\vibecoding` being importable (or `DATA_WAREHOUSE` / path setup).
