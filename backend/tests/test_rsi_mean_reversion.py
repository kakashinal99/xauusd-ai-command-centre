from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.market_data.schemas import CandleInput
from app.strategy.rsi_mean_reversion import generate_rsi_mean_reversion_signals, simple_rsi
from app.strategy.schemas import RsiMeanReversionConfig


def make_candles(closes):
    rows = []
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    previous = Decimal(str(closes[0]))
    for i, value in enumerate(closes):
        close = Decimal(str(value))
        open_price = previous
        rows.append(CandleInput(
            timeframe="M15", open_time=start + timedelta(minutes=15 * i),
            open=open_price, high=max(open_price, close) + Decimal("1"),
            low=min(open_price, close) - Decimal("1"), close=close,
        ))
        previous = close
    return rows


def test_simple_rsi_is_bounded_and_waits_for_full_period():
    candles = make_candles([100, 99, 98, 97, 96, 97, 98, 99])
    values = simple_rsi(candles, 3)
    assert values[:3] == [None, None, None]
    assert all(value is None or Decimal("0") <= value <= Decimal("100") for value in values)


def test_rsi_mean_reversion_emits_valid_signal_after_oversold_recovery():
    closes = [100, 99, 98, 97, 96, 95, 94, 95, 96, 97, 98, 99, 100, 99, 98, 97, 96, 95, 94, 95, 96]
    candles = make_candles(closes)
    config = RsiMeanReversionConfig(
        rsi_period=3, atr_period=3, oversold=Decimal("30"),
        overbought=Decimal("70"), atr_stop_multiple=Decimal("1"),
        reward_risk_ratio=Decimal("2"),
    )
    signals = generate_rsi_mean_reversion_signals(candles, config)
    assert signals
    assert all(signal.direction in {"long", "short"} for signal in signals)
    assert all(signal.take_profit > ZERO for signal in signals)


ZERO = Decimal("0")
