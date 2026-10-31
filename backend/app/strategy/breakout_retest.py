"""Close-confirmed breakout and retest strategy.

A breakout is only eligible after a candle closes beyond the prior range.
Entry signal requires a later candle to revisit the broken level and close
back on the breakout side. The backtester enters at the following candle open.
This is a mechanical research baseline, not a claim of profitability.
"""
from app.backtesting.schemas import TradeSignal
from app.market_data.schemas import CandleInput
from app.strategy.indicators import simple_atr
from app.strategy.schemas import BreakoutRetestConfig


def generate_breakout_retest_signals(
    candles: list[CandleInput], config: BreakoutRetestConfig | None = None
) -> list[TradeSignal]:
    config = config or BreakoutRetestConfig()
    minimum = max(config.lookback, config.atr_period)
    if len(candles) <= minimum + 1:
        return []

    atr_values = simple_atr(candles, config.atr_period)
    pending = None
    signals: list[TradeSignal] = []

    for index in range(minimum, len(candles)):
        candle = candles[index]
        atr = atr_values[index]
        if atr is None or atr <= 0:
            continue

        # Expire a setup after the configured number of completed retest bars.
        if pending is not None and index - pending["breakout_index"] > config.retest_window:
            pending = None

        if pending is not None:
            level = pending["level"]
            tolerance = atr * config.retest_tolerance_atr
            direction = pending["direction"]
            if direction == "long":
                touched = candle.low <= level + tolerance
                held = candle.close > level and candle.close >= candle.open
            else:
                touched = candle.high >= level - tolerance
                held = candle.close < level and candle.close <= candle.open

            if touched and held:
                if direction == "long":
                    stop = candle.low - atr * config.stop_atr_buffer
                    distance = candle.close - stop
                    target = candle.close + distance * config.reward_risk_ratio
                    if stop > 0 and distance > 0:
                        signals.append(TradeSignal(
                            signal_time=candle.open_time,
                            direction="long",
                            stop_loss=stop,
                            take_profit=target,
                        ))
                else:
                    stop = candle.high + atr * config.stop_atr_buffer
                    distance = stop - candle.close
                    target = candle.close - distance * config.reward_risk_ratio
                    if target > 0 and distance > 0:
                        signals.append(TradeSignal(
                            signal_time=candle.open_time,
                            direction="short",
                            stop_loss=stop,
                            take_profit=target,
                        ))
                pending = None
                continue

        # Do not treat the same candle as both breakout and retest.
        prior = candles[index - config.lookback:index]
        prior_high = max(item.high for item in prior)
        prior_low = min(item.low for item in prior)
        if candle.close > prior_high:
            pending = {
                "direction": "long",
                "level": prior_high,
                "breakout_index": index,
            }
        elif candle.close < prior_low:
            pending = {
                "direction": "short",
                "level": prior_low,
                "breakout_index": index,
            }

    return signals
