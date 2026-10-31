# Multi-Strategy Comparison and Market Regimes

## Endpoint

`POST /api/v1/research/compare-strategies`

The endpoint runs every strategy currently registered in the research comparison registry against the same XAUUSD candle dataset and common execution assumptions.

Currently registered:
- `donchian_atr`: Donchian breakout with ATR stop.
- `dow_candlestick`: confirmed Dow swing structure with candlestick confirmation.
- `rsi_mean_reversion`: enters when RSI recovers back above oversold or back below overbought, with an ATR-based stop.\n- `breakout_retest`: requires a close beyond the prior range, followed by a bounded retest and close back on the breakout side; uses an ATR-buffered stop.

The registry is intentionally explicit. Adding a strategy requires registering its signal generator and configuration in `app/research/comparison.py`.

## Market regime labels

Each candle is assigned one heuristic label using completed OHLC candles:
- `trending`: rolling close-to-close efficiency ratio >= 0.35.
- `ranging`: efficiency ratio <= 0.20.
- `high_volatility`: current normalized high-low range is at or above the rolling 80th-percentile threshold, after a minimum reference sample.
- `transition`: insufficient history or mixed/unclear conditions.

High volatility takes precedence over trend/range labels. The classifier is deliberately transparent and deterministic. It is not an ML prediction and thresholds are not yet calibrated for XAUUSD timeframes.

## Attribution

Each strategy returns:
- overall backtest metrics;
- trade count, return, profit factor, expectancy, win rate and max drawdown for signals whose signal candle was assigned to each regime.

Each regime subset is backtested independently from the same initial equity. Therefore, per-regime returns are diagnostic standalone simulations, not additive components of the overall strategy return. Trades may cross into a later regime; attribution uses the regime at signal time.

## Safety and limitations

- Research only. No strategy is automatically selected and no orders are sent.
- Four registered strategies are currently included; this is not yet an exhaustive strategy library.\n- Breakout/retest is a simplified mechanical rule: it does not yet model higher-timeframe levels, liquidity sweeps, order-flow confirmation or session filters. A retest must occur within the configured bar window.
- RSI uses a simple rolling average (not Wilder RSI); it is a transparent research baseline, not a validated XAUUSD edge. Mean reversion may perform poorly during persistent directional moves.
- The existing OHLC engine uses simplified abstract XAUUSD quantity, not Pepperstone contract/lot sizing.
- Spread, slippage and commission defaults are zero unless supplied. Realistic broker costs must be configured before interpreting results.
- Regime thresholds and strategy parameters require out-of-sample and walk-forward validation.
- Avoid selecting a strategy based on the best historical regime result alone. Require sufficient trade count, stable expectancy, acceptable drawdown and repeated out-of-sample performance.
