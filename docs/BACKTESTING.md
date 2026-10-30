# Backtesting Engine (Phase 1)

This module adds a deterministic, in-memory XAUUSD OHLC backtester. It does **not** connect to cTrader, place orders, discover strategies, or enable live trading.

## Execution assumptions

- A signal is available only after its candle closes. Entry is at the **next candle open**; there is no same-candle look-ahead entry.
- Only one position is held at a time. Signals while a position is open are ignored.
- Quantity is abstract XAUUSD units: risk cash divided by entry-to-stop price distance. Pepperstone contract size, lot step, minimum volume, tick value, and account-currency conversion are not guessed. Broker symbol metadata is required before translating quantity into lots.
- Spread is charged as half-spread on each side; slippage is adverse on entry and exit. Commission is a round-trip cost per abstract unit.
- If a candle touches both stop loss and take profit, stop loss is assumed first (conservative OHLC-only rule).
- A gap through the stop exits at the candle open. A gap beyond the target is filled at the target, not at a better price.
- Any still-open position is closed at the final candle close and labelled end_of_data.

## Inputs and outputs

BacktestRequest accepts normalized CandleInput candles, timestamped TradeSignal objects, and BacktestConfig. The engine reports trade-level entries/exits, net P&L, return, win rate, gross profit/loss, profit factor, expectancy, maximum peak-to-trough drawdown, and an equity curve.

## Limitations before strategy validation

- No strategy indicator or signal generator is included yet. Signals are supplied as input so execution assumptions can be tested independently.
- No funding/financing, swap, variable spread, market sessions, news filters, partial fills, broker commission schedule, or broker-specific contract sizing yet.
- Results are not evidence of an edge. Before any strategy can progress, add verified broker data, realistic symbol economics, out-of-sample and walk-forward testing, and Monte Carlo analysis.
- The engine is research-only. It is not wired to the risk gate or an execution adapter and cannot submit orders.
