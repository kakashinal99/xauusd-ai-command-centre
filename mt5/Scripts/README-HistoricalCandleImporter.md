# Historical Candle Importer (MT5)

This is a one-shot, read-only script. It copies closed OHLC bars from the currently logged-in MT5 broker into the XAUUSD AI Command Centre database. It does not place or modify trades.

## Install

1. In MT5 choose **File → Open Data Folder**.
2. Open `MQL5/Scripts` (create the folder if it does not exist).
3. Copy `HistoricalCandleImporter.mq5` into that folder.
4. Open MetaEditor, locate the script under **Scripts**, and press **F7** to compile.
5. In MT5 open **Tools → Options → Expert Advisors** and add this exact URL under **Allow WebRequest for listed URL**:
   `https://xauusd-ai-command-centre-api.onrender.com`

## Run an import

1. Open a Pepperstone chart for the instrument you want (for example XAUUSD).
2. Press **Home** repeatedly on the chart to make MT5 download older history. MT5's **Max bars in chart** setting may need to be increased.
3. Drag **HistoricalCandleImporter** from Navigator → Scripts onto that chart.
4. Set:
   - `IngestUrl`: leave the default.
   - `IngestKey`: paste the same private value configured as Render's `INGEST_API_KEY`. Do not share it.
   - `CanonicalSymbol`: `XAUUSD` (even if the broker chart has a suffix).
   - `ImportTimeframe`: start with `PERIOD_M1`.
   - `BarsToImport`: start with `10000`; increase only after a successful test.
   - `BatchSize`: leave at `500`.
5. Click OK. Watch the **Experts** tab for progress and the final stored/failed counts.

## Notes

- Import uses closed bars only; the current forming candle is excluded.
- Run again with a larger `BarsToImport` to extend history. The backend upserts on symbol + timeframe + candle open time, so reruns do not create duplicate candles.
- Repeat for M5, M15, H1, etc. only when those timeframes are needed. M1 can be resampled into higher timeframes later.
- MT5 can only import history that the terminal has actually downloaded and the broker makes available.
- Broker server timestamps are converted to UTC using the terminal's current server/GMT offset. Verify timestamps around broker daylight-saving changes before relying on multi-year intraday tests.
- This importer stores OHLC and tick volume. It does **not** import historical bid/ask ticks. Accurate tick-level testing requires a separate tick-history source/export.
- A successful MT5 script message means the API accepted the batch. Verify the database totals in the dashboard/API summary before running a backtest.
