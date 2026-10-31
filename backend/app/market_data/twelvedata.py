"""Twelve Data adapter for XAU/USD market data.

This module only retrieves market data. It does not place or manage trades.
The provider's price stream is a single-price event, not a guaranteed broker bid/ask.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import httpx

from app.config import get_settings


class MarketDataProviderError(RuntimeError):
    pass


class TwelveDataProvider:
    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.twelve_data_api_key:
            raise MarketDataProviderError("TWELVE_DATA_API_KEY is not configured")

    async def latest_price(self) -> dict[str, Any]:
        params = {
            "symbol": self.settings.twelve_data_symbol,
            "apikey": self.settings.twelve_data_api_key,
        }
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(f"{self.settings.twelve_data_rest_base_url}/price", params=params)
            response.raise_for_status()
            payload = response.json()
        if payload.get("status") == "error" or "price" not in payload:
            raise MarketDataProviderError(str(payload))
        return {
            "symbol": "XAUUSD",
            "provider_symbol": payload.get("symbol", self.settings.twelve_data_symbol),
            "price": Decimal(str(payload["price"])),
            "event_time": datetime.now(timezone.utc),
            "source": "twelvedata",
        }

    async def m1_candles(self, outputsize: int = 500) -> list[dict[str, Any]]:
        params = {
            "symbol": self.settings.twelve_data_symbol,
            "interval": "1min",
            "outputsize": max(1, min(outputsize, 5000)),
            "apikey": self.settings.twelve_data_api_key,
            "timezone": "UTC",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{self.settings.twelve_data_rest_base_url}/time_series", params=params)
            response.raise_for_status()
            payload = response.json()
        if payload.get("status") == "error" or not isinstance(payload.get("values"), list):
            raise MarketDataProviderError(str(payload))
        candles = []
        for item in reversed(payload["values"]):
            opened = datetime.strptime(item["datetime"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            candles.append({
                "symbol": "XAUUSD",
                "timeframe": "M1",
                "open_time": opened.isoformat(),
                "open": item["open"],
                "high": item["high"],
                "low": item["low"],
                "close": item["close"],
                "volume": item.get("volume"),
                "source": "twelvedata",
            })
        return candles
