# Dow Theory + Candlestick Confirmation Strategy

This is a separate research strategy for XAUUSD. It combines confirmed Dow swing structure with a closed-candle confirmation.

## Dow Theory structure

- Bullish regime: the latest two confirmed swing highs form a Higher High (HH), and the latest two confirmed swing lows form a Higher Low (HL).
- Bearish regime: the latest two confirmed swing highs form a Lower High (LH), and the latest two confirmed swing lows form a Lower Low (LL).
- A swing high/low is confirmed only after the configured number of right-side candles have closed. Until then it is unavailable to the strategy.
- If high and low structure disagree, the regime is neutral and no trade is generated.

## Candle confirmation

- Bullish confirmation in a bullish regime: bullish engulfing OR hammer-shaped lower-wick rejection.
- Bearish confirmation in a bearish regime: bearish engulfing OR shooting-star-shaped upper-wick rejection.
- Engulfing requires the current candle body to cover the previous opposite-colour candle body.
- Hammer / shooting star require the dominant wick to be at least the configured multiple of the real body, while the opposite wick cannot exceed the body.

## Risk and execution

- Signal timestamp is the confirmation candle close; the backtester enters on the next candle open.
- Stop is beyond the signal candle extreme with an ATR buffer.
- Target is based on the configured reward-to-risk ratio.
- The strategy only generates research signals; it does not place orders or bypass the independent risk engine.

## Parameters

Pivot left/right bars, ATR period, ATR stop buffer, reward-to-risk ratio, and wick-to-body ratio are configurable. Defaults are generic and must be tested, not assumed optimal.

## Research warning

This is a mechanical interpretation of Dow Theory and selected candlestick patterns, not a complete discretionary Dow Theory system. Candlestick names are not sufficient evidence of edge. Validate on Pepperstone cTrader historical XAUUSD data with realistic symbol economics, out-of-sample and walk-forward tests, and Monte Carlo analysis before considering deployment.

## API endpoint

Research endpoint: POST /api/v1/research/backtest/dow-candlestick. It accepts chronological validated XAUUSD candles, strategy parameters, initial equity, risk percentage, spread, slippage, and commission. The response uses the common backtest result schema. It cannot connect to the broker or execute trades.
