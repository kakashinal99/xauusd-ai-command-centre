from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.market_data.schemas import CandleInput, normalize_candles


def candle(minute: int, close: str = "2350.5") -> CandleInput:
    return CandleInput(
        timeframe="M1",
        open_time=datetime(2026, 1, 1, 0, minute, tzinfo=timezone.utc),
        open=Decimal("2350.0"),
        high=Decimal("2351.0"),
        low=Decimal("2349.0"),
        close=Decimal(close),
    )


def test_candles_are_sorted_and_duplicate_key_keeps_latest_value() -> None:
    first = candle(2)
    replacement = candle(2, "2350.8")
    earlier = candle(1)
    result = normalize_candles([first, earlier, replacement])
    assert [item.open_time.minute for item in result] == [1, 2]
    assert result[-1].close == Decimal("2350.8")


def test_rejects_non_xauusd_symbol() -> None:
    with pytest.raises(ValidationError):
        CandleInput(
            symbol="EURUSD", timeframe="M1",
            open_time=datetime.now(timezone.utc),
            open=1, high=1, low=1, close=1,
        )


def test_rejects_invalid_ohlc() -> None:
    with pytest.raises(ValidationError):
        CandleInput(
            timeframe="M1", open_time=datetime.now(timezone.utc),
            open=10, high=9, low=8, close=9,
        )
