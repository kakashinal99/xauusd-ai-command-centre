from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.market_data.schemas import CandleInput
from app.strategy.breakout_retest import generate_breakout_retest_signals
from app.strategy.schemas import BreakoutRetestConfig


def test_breakout_retest_waits_for_retest_confirmation():
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    raw = [
        ("100", "101", "99", "100"),
        ("100", "101", "99", "100"),
        ("100", "101", "99", "100"),
        ("100", "104", "99", "103"),  # close above prior range
        ("102", "103", "100.5", "102.5"),  # retest and bullish close
        ("102.5", "104", "102", "103.5"),
    ]
    candles = [
        CandleInput(
            timeframe="M15",
            open_time=start + timedelta(minutes=15 * i),
            open=Decimal(o), high=Decimal(h), low=Decimal(l), close=Decimal(c),
        )
        for i, (o, h, l, c) in enumerate(raw)
    ]
    config = BreakoutRetestConfig(
        lookback=3,
        retest_window=3,
        atr_period=2,
        retest_tolerance_atr=Decimal("0.5"),
        stop_atr_buffer=Decimal("0.1"),
        reward_risk_ratio=Decimal("2"),
    )
    signals = generate_breakout_retest_signals(candles, config)
    assert len(signals) == 1
    assert signals[0].direction == "long"
    assert signals[0].signal_time == candles[4].open_time
    assert signals[0].stop_loss < Decimal("100.5")
    assert signals[0].take_profit > Decimal("102.5")


def test_breakout_without_retest_does_not_emit_signal():
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    raw = [
        (100, 101, 99, 100), (100, 101, 99, 100),
        (100, 101, 99, 100), (100, 104, 99, 103),
        (104.5, 106, 104.2, 105.5), (105.5, 107, 105.2, 106.5),
        (106.5, 108, 106.2, 107.5),
    ]
    candles = [CandleInput(
        timeframe="M15",
        open_time=start + timedelta(minutes=15 * i),
        open=Decimal(str(o)), high=Decimal(str(h)),
        low=Decimal(str(l)), close=Decimal(str(c)),
    ) for i, (o, h, l, c) in enumerate(raw)]
    config = BreakoutRetestConfig(
        lookback=3, retest_window=2, atr_period=2,
        retest_tolerance_atr=Decimal("0.1"),
    )
    assert generate_breakout_retest_signals(candles, config) == []
