from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.market_data.schemas import CandleInput
from app.strategy.dow_candlestick import (
    _bearish_engulfing, _bullish_engulfing, _hammer, _shooting_star, _confirmed_pivots,
    generate_dow_candlestick_signals,
)
from app.strategy.schemas import DowCandlestickConfig


def c(i, o, h, l, close):
    return CandleInput(timeframe="M1", open_time=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=i),
        open=Decimal(str(o)), high=Decimal(str(h)), low=Decimal(str(l)), close=Decimal(str(close)))


def test_bullish_and_bearish_engulfing_patterns():
    assert _bullish_engulfing(c(0, 10, 10.5, 8.5, 9), c(1, 8.8, 11, 8.7, 10.2))
    assert _bearish_engulfing(c(0, 9, 10.5, 8.5, 10), c(1, 10.2, 10.3, 8, 8.8))


def test_hammer_and_shooting_star_wick_rules():
    assert _hammer(c(0, 10, 10.2, 8, 10.1), Decimal("2"))
    assert _shooting_star(c(0, 10, 12, 9.9, 10.1), Decimal("2"))


def test_strategy_returns_no_signals_without_enough_history():
    candles = [c(i, 100, 101, 99, 100) for i in range(8)]
    config = DowCandlestickConfig(pivot_left=2, pivot_right=2, atr_period=3)
    assert generate_dow_candlestick_signals(candles, config) == []


def test_pivot_is_timestamped_when_right_side_confirmation_completes():
    candles = [
        c(0, 10, 11, 9, 10),
        c(1, 10, 12, 9, 11),
        c(2, 11, 15, 10, 14),
        c(3, 14, 13, 10, 11),
        c(4, 11, 12, 8, 9),
    ]
    highs, lows = _confirmed_pivots(candles, left=1, right=1)
    assert (3, Decimal("15")) in highs
