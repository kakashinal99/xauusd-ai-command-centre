# Market data pipeline

## Current status
The provider-neutral contract and PostgreSQL storage models are in place. The cTrader adapter is intentionally not connected yet because the Open API application is still awaiting approval.

## Data model
- `market_candles`: normalized OHLCV bars keyed by symbol, timeframe and candle open time.
- `market_ticks`: timestamped bid/ask observations.
- `market_data_checkpoints`: ingestion cursor for safe restart and catch-up.

## Rules
- Only XAUUSD is accepted by the current candle contract.
- All timestamps must be timezone-aware and are normalized to UTC.
- OHLC prices must be positive and internally consistent.
- Candle ingestion is designed to be idempotent using the unique symbol/timeframe/open-time key.
- Historical requests must respect cTrader's documented request limits when the adapter is implemented.
- This pipeline is read-only; it has no order placement capability.

## Next implementation step
Implement the cTrader OAuth flow and a read-only historical/live market-data adapter after application approval. Add migrations and integration tests before enabling persistent ingestion.
