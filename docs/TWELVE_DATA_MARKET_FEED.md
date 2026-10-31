# Twelve Data market feed adapter

This adapter retrieves XAU/USD prices and M1 candles from Twelve Data. It is a **market-data integration only**; it does not connect to a broker or submit orders.

## Environment

Set these on the backend service (never in the browser):

- `TWELVE_DATA_API_KEY`: API key from your Twelve Data account.
- `TWELVE_DATA_SYMBOL`: defaults to `XAU/USD`.
- `TWELVE_DATA_REST_BASE_URL`: defaults to `https://api.twelvedata.com`.
- `TWELVE_DATA_WS_URL`: defaults to `wss://ws.twelvedata.com/v1/quotes/price`.

## Current adapter scope

- `TwelveDataProvider.latest_price()`: REST latest-price request.
- `TwelveDataProvider.m1_candles()`: REST M1 OHLC history request.
- The WebSocket URL and symbol settings are prepared for the streaming worker, but no always-on streaming worker is enabled by this commit.
- The provider's price endpoint/stream supplies a single price, not an exchange-style bid/ask pair. Do not fabricate bid/ask or use this mid/last price as an executable broker quote.

## Next integration stage

1. Confirm XAU/USD access and actual WebSocket entitlement on the chosen Twelve Data plan.
2. Add a dedicated always-on worker that subscribes to the price stream, reconnects with backoff, and posts ticks to the protected ingestion endpoint.
3. Backfill M1 candles via REST and persist them through the ingestion endpoint.
4. Validate timestamps, gaps, freshness, provider-vs-broker basis and data licensing before signals are enabled.

A Twelve Data API key is not required in GitHub. Add it as a secret environment variable in the backend host.
