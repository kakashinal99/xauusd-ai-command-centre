"""Market data provider interface; concrete cTrader adapter is added after API approval."""

from abc import ABC, abstractmethod
from datetime import datetime

from app.market_data.schemas import CandleInput


class MarketDataProvider(ABC):
    @abstractmethod
    async def get_historical_candles(
        self, symbol: str, timeframe: str, start: datetime, end: datetime
    ) -> list[CandleInput]:
        """Fetch candles for a time range. Implementations must be read-only."""
        raise NotImplementedError

    @abstractmethod
    async def connect(self) -> None:
        """Establish the provider connection without placing trades."""
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        """Close the provider connection cleanly."""
        raise NotImplementedError
