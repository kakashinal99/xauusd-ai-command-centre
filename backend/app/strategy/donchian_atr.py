"""Baseline Donchian breakout strategy used to validate the research pipeline.

This is an engineering example, not the user's proprietary trading strategy and
not a claim that the rules have a profitable edge.
"""

from app.backtesting.schemas import TradeSignal
from app.market_data.schemas import CandleInput
from app.strategy.indicators import simple_atr
from app.strategy.schemas import DonchianAtrConfig


def generate_donchian_atr_signals(
    candles: list[CandleInput], config: DonchianAtrConfig | None = None
) -> list[TradeSignal]:
    config = config or DonchianAtrConfig()
    if len(candles) <= max(config.lookback, config.atr_period):
        return []
    atr_values = simple_atr(candles, config.atr_period)
    signals: list[TradeSignal] = []
    for index in range(max(config.lookback, config.atr_period - 1), len(candles)):
        atr = atr_values[index]
        if atr is None or atr <= 0:
            continue
        prior = candles[index - config.lookback:index]
        prior_high = max(c.high for c in prior)
        prior_low = min(c.low for c in prior)
        current = candles[index]
        if current.close > prior_high:
            distance = atr * config.atr_stop_multiple
            signals.append(TradeSignal(
                signal_time=current.open_time,
                direction="long",
                stop_loss=current.close - distance,
                take_profit=current.close + distance * config.reward_risk_ratio,
            ))
        elif current.close < prior_low:
            distance = atr * config.atr_stop_multiple
            signals.append(TradeSignal(
                signal_time=current.open_time,
                direction="short",
                stop_loss=current.close + distance,
                take_profit=current.close - distance * config.reward_risk_ratio,
            ))
    return signals
