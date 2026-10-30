"""Small, deterministic indicator functions with no external data dependencies."""

from decimal import Decimal

from app.market_data.schemas import CandleInput

ZERO = Decimal("0")


def true_ranges(candles: list[CandleInput]) -> list[Decimal]:
    ranges: list[Decimal] = []
    previous_close = None
    for candle in candles:
        intrabar = candle.high - candle.low
        if previous_close is None:
            ranges.append(intrabar)
        else:
            ranges.append(max(intrabar, abs(candle.high - previous_close), abs(candle.low - previous_close)))
        previous_close = candle.close
    return ranges


def simple_atr(candles: list[CandleInput], period: int) -> list[Decimal | None]:
    """SMA of true range; values are None until a full period is available."""
    if period < 1:
        raise ValueError("period must be positive")
    ranges = true_ranges(candles)
    output: list[Decimal | None] = [None] * len(candles)
    rolling = ZERO
    for index, value in enumerate(ranges):
        rolling += value
        if index >= period:
            rolling -= ranges[index - period]
        if index >= period - 1:
            output[index] = rolling / Decimal(period)
    return output
