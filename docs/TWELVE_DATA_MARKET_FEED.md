# Twelve Data market feed integration

This integration is for market data only. It does not connect to a broker or submit trades.

## Backend environment

- `TWELVE_DATA_API_KEY`: secret key from Twelve Data.
- `TWELVE_DATA_SYMBOL`: defaults to `XAU/USD`.
- `BACKEND_INTERNAL_URL`: URL reachable by the worker; defaults to `http://localhost:8000`.
- `INGEST_API_KEY`: same secret configured on the backend ingestion API.
- `DATABASE_URL`: PostgreSQL connection string.

Keep all keys in hosting-provider secret settings, never in frontend code or Git.

## Components

- `TwelveDataProvider.latest_price()`: REST latest-price request.
- `TwelveDataProvider.m1_candles()`: REST historical M1 candles.
- `python -m app.market_data.twelvedata_worker`: standalone WebSocket worker with reconnect/backoff and M1 history backfill.
- Tick storage has a dedicated `price` field for single-price provider events; it does not fabricate bid/ask.

## Deployment sequence

1. Apply `migrations/20261031_add_market_tick_price.sql` to an existing database before deploying the model change.
2. Configure `TWELVE_DATA_API_KEY`, `INGEST_API_KEY`, `DATABASE_URL`, and `BACKEND_INTERNAL_URL`.
3. Deploy the backend.
4. Run a dedicated always-on worker with `cd backend && python -m app.market_data.twelvedata_worker`.
5. Confirm provider subscription acknowledgement, tick timestamps, M1 history and database counts.
6. Verify the chosen Twelve Data plan explicitly includes XAU/USD streaming. REST access does not prove WebSocket entitlement.

## Important limitations

Provider prices are not guaranteed executable broker bid/ask quotes. Measure basis differences against the intended broker feed before using this data for trading decisions. WebSocket access and delivery characteristics depend on the subscription. Redistribution to subscribers may require a separate commercial data licence.
