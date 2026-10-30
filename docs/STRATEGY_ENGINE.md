# Strategy Signal Engine (Phase 1)

The strategy layer now includes reusable true-range / simple-ATR calculations and a baseline Donchian breakout with ATR-based stops and configurable reward-to-risk targets.

## Baseline rules

- Long when the current candle closes above the highest high of the preceding N candles.
- Short when the current candle closes below the lowest low of the preceding N candles.
- The current candle is excluded from the breakout range to avoid comparing the close against a range that includes its own high/low.
- Stop distance is ATR multiplied by a configurable factor; take profit is that distance multiplied by the configured reward-to-risk ratio.
- A signal is timestamped at the candle close. The backtester enters no earlier than the next candle open.

## Important distinction

This Donchian/ATR strategy is a **pipeline test strategy only**. It is not the user's 1-2-3 / market-structure / price-action strategy, and no profitability is implied. The user's actual rules must be specified precisely and implemented as a separate strategy before its results are evaluated.

## Limitations

- ATR is a simple moving average of true range, not Wilder's smoothed ATR.
- No parameter optimization, strategy discovery, AI-generated rule mutation, or live activation is included.
- Always test with realistic broker spread, slippage, commission, symbol contract details, out-of-sample periods, and walk-forward validation.

## API endpoint

A research-only endpoint is available at `POST /api/v1/research/backtest/donchian-atr`. Submit chronological validated XAUUSD candles, optional Donchian/ATR settings, starting equity, risk percentage, spread, slippage, and commission. It returns the backtest metrics and trade list. The endpoint does not access cTrader or execute orders.
