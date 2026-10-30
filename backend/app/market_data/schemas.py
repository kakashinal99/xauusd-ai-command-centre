"""Provider-neutral market data contracts."""

from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class CandleInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    symbol: str = "XAUUSD"
    timeframe: str
    open_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal | None = None
    source: str = "ctrader"

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized != "XAUUSD":
            raise ValueError("This deployment is restricted to XAUUSD")
        return normalized

    @field_validator("open_time")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("open_time must include a timezone")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def validate_ohlc(self):
        if min(self.open, self.high, self.low, self.close) <= 0:
            raise ValueError("OHLC prices must be positive")
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high must be the highest OHLC value")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low must be the lowest OHLC value")
        if self.volume is not None and self.volume < 0:
            raise ValueError("volume cannot be negative")
        return self


def normalize_candles(candles: list[CandleInput]) -> list[CandleInput]:
    """Return unique candles in chronological order; newest duplicate wins."""
    by_key = {(c.symbol, c.timeframe, c.open_time): c for c in candles}
    return sorted(by_key.values(), key=lambda c: c.open_time)
