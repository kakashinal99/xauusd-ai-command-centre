"""Dow Theory trend structure with candlestick confirmation.

Swing points are only confirmed after right_bars have closed, avoiding
look-ahead bias in historical signal generation.
"""
from decimal import Decimal

from app.backtesting.schemas import TradeSignal
from app.market_data.schemas import CandleInput
from app.strategy.indicators import simple_atr
from app.strategy.schemas import DowCandlestickConfig

ZERO = Decimal("0")


def _confirmed_pivots(candles: list[CandleInput], left: int, right: int):
    highs: list[tuple[int, Decimal]] = []
    lows: list[tuple[int, Decimal]] = []
    for index in range(left + right, len(candles)):
        pivot_index = index - right
        window = candles[pivot_index - left:pivot_index + right + 1]
        pivot = candles[pivot_index]
        if all(pivot.high > c.high for offset, c in enumerate(window) if offset != left):
            highs.append((index, pivot.high))
        if all(pivot.low < c.low for offset, c in enumerate(window) if offset != left):
            lows.append((index, pivot.low))
    return highs, lows


def _trend_at(highs, lows, candle_index: int) -> str | None:
    known_highs = [price for confirmed_at, price in highs if confirmed_at < candle_index]
    known_lows = [price for confirmed_at, price in lows if confirmed_at < candle_index]
    if len(known_highs) < 2 or len(known_lows) < 2:
        return None
    if known_highs[-1] > known_highs[-2] and known_lows[-1] > known_lows[-2]:
        return "bullish"
    if known_highs[-1] < known_highs[-2] and known_lows[-1] < known_lows[-2]:
        return "bearish"
    return None


def _bullish_engulfing(previous, current) -> bool:
    return (previous.close < previous.open and current.close > current.open
            and current.open <= previous.close and current.close >= previous.open)


def _bearish_engulfing(previous, current) -> bool:
    return (previous.close > previous.open and current.close < current.open
            and current.open >= previous.close and current.close <= previous.open)


def _hammer(current, wick_body_ratio: Decimal) -> bool:
    body = abs(current.close - current.open)
    if body == ZERO:
        return False
    lower = min(current.open, current.close) - current.low
    upper = current.high - max(current.open, current.close)
    return lower >= body * wick_body_ratio and upper <= body


def _shooting_star(current, wick_body_ratio: Decimal) -> bool:
    body = abs(current.close - current.open)
    if body == ZERO:
        return False
    upper = current.high - max(current.open, current.close)
    lower = min(current.open, current.close) - current.low
    return upper >= body * wick_body_ratio and lower <= body


def generate_dow_candlestick_signals(
    candles: list[CandleInput], config: DowCandlestickConfig | None = None
) -> list[TradeSignal]:
    config = config or DowCandlestickConfig()
    minimum = config.pivot_left + config.pivot_right + config.atr_period + 4
    if len(candles) < minimum:
        return []
    atr_values = simple_atr(candles, config.atr_period)
    highs, lows = _confirmed_pivots(candles, config.pivot_left, config.pivot_right)
    signals: list[TradeSignal] = []

    for index in range(1, len(candles)):
        atr = atr_values[index]
        if atr is None or atr <= ZERO:
            continue
        trend = _trend_at(highs, lows, index)
        previous, current = candles[index - 1], candles[index]
        bullish_pattern = _bullish_engulfing(previous, current) or _hammer(current, config.wick_body_ratio)
        bearish_pattern = _bearish_engulfing(previous, current) or _shooting_star(current, config.wick_body_ratio)
        if trend == "bullish" and bullish_pattern:
            stop = current.low - atr * config.stop_atr_buffer
            risk = current.close - stop
            if risk > ZERO:
                signals.append(TradeSignal(signal_time=current.open_time, direction="long",
                    stop_loss=stop, take_profit=current.close + risk * config.reward_risk_ratio))
        elif trend == "bearish" and bearish_pattern:
            stop = current.high + atr * config.stop_atr_buffer
            risk = stop - current.close
            target = current.close - risk * config.reward_risk_ratio
            if risk > ZERO and target > ZERO:
                signals.append(TradeSignal(signal_time=current.open_time, direction="short",
                    stop_loss=stop, take_profit=target))
    return signals
