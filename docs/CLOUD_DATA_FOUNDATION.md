# Cloud data foundation

## Scope
The API stores normalized XAUUSD market candles and bid/ask ticks in PostgreSQL. It is broker-neutral: cTrader credentials and connection code are deliberately absent. No endpoint submits trading orders.

## Services
- FastAPI backend on Render (Singapore)
- Render PostgreSQL for candle/tick history
- Render Key Value (Valkey) reserved for cache/fanout; not the source of truth
- Next.js frontend remains a separate service

## API
- GET /health — process health
- GET /api/v1/status — trading remains disabled
- GET /api/v1/market-data/summary — stored row counts and latest timestamps
- POST /api/v1/market-data/candles/batch — validated, idempotent candle upsert (max 5,000 per request)
- POST /api/v1/market-data/ticks/batch — validated tick insert (max 10,000 per request)
- GET /api/v1/market-data/candles?timeframe=M1&limit=500 — recent candles

All timestamps must include a timezone and are normalized to UTC. Only XAUUSD is accepted. PostgreSQL is authoritative; cache loss must never delete historical market data.

## Safety and limitations
- cTrader provider/OAuth is not connected.
- Ingestion endpoints currently require a trusted network boundary; add authentication/rate limiting before exposing a collector publicly.
- No live or historical broker data is fabricated. Until cTrader is connected, row counts should remain zero.
- The free Render Postgres instance is temporary and expires on 2026-11-30 unless upgraded or migrated before expiry. Free Key Value has persistence disabled and is cache-only.
- Trading and order execution remain disabled.
