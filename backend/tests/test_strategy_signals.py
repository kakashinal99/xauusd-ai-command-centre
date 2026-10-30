from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.market_data.schemas import CandleInput
from app.strategy.donchian_atr import generate_donchian_atr_signals
from app.strategy.schemas import DonchianAtrConfig
from app.strategy.indicators import simple_atr


def make_candles(rows):
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [CandleInput(
        timeframe="M1", open_time=base + timedelta(minutes=i),
        open=Decimal(str(o)), high=Decimal(str(h)), low=Decimal(str(l)), close=Decimal(str(c)),
    ) for i, (o, h, l, c) in enumerate(rows)]


def test_atr_is_unavailable_until_full_period():
    candles = make_candles([(100, 101, 99, 100), (100, 102, 99, 101), (101, 103, 100, 102)])
    values = simple_atr(candles, 2)
    assert values[0] is None
    assert values[1] is not None
    assert values[2] is not None


def test_donchian_breakout_signal_uses_prior_bars_only():
    candles = make_candles([
        (100, 101, 99, 100), (100, 101, 99, 100),
        (100, 101, 99, 100), (100, 104, 100, 103),
    ])
    config = DonchianAtrConfig(lookback=3, atr_period=2, atr_stop_multiple=Decimal("1"), reward_risk_ratio=Decimal("2"))
    signals = generate_donchian_atr_signals(candles, config)
    assert len(signals) == 1
    assert signals[0].direction == "long"
    assert signals[0].signal_time == candles[3].open_time
    assert signals[0].stop_loss < candles[3].close < signals[0].take_profit


def test_no_signal_when_history_is_too_short():
    candles = make_candles([(100, 101, 99, 100), (100, 101, 99, 100)])
    assert generate_donchian_atr_signals(candles, DonchianAtrConfig(lookback=3, atr_period=2)) == []
