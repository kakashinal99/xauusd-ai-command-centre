"""Standalone Twelve Data ingestion worker; no trade execution."""
import asyncio
import json
import logging
import random
from datetime import datetime, timezone
import httpx
import websockets
from app.config import get_settings
from app.market_data.twelvedata import TwelveDataProvider

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("market-feed")

async def post(client, base, key, endpoint, payload):
    response = await client.post(f"{base}/api/v1/market-data/{endpoint}", json=payload,
                                 headers={"X-Ingest-Key": key})
    response.raise_for_status()

async def run():
    settings = get_settings()
    if not settings.ingest_api_key:
        raise RuntimeError("INGEST_API_KEY is required")
    provider = TwelveDataProvider()
    symbol = provider.symbol
    base = settings.backend_internal_url.rstrip("/")
    url = f"{settings.twelve_data_ws_url}?apikey={settings.twelve_data_api_key}"
    delay = 2
    async with httpx.AsyncClient(timeout=25) as client:
        while True:
            try:
                history = await provider.m1_candles(500)
                if history:
                    await post(client, base, settings.ingest_api_key, "candles/batch", {"candles": history})
                    log.info("Backfilled %s M1 candles for %s", len(history), symbol)
                async with websockets.connect(url, ping_interval=20, ping_timeout=20,
                                              close_timeout=10, max_size=2**20) as ws:
                    await ws.send(json.dumps({"action": "subscribe",
                                              "params": {"symbols": settings.twelve_data_symbol}}))
                    log.info("WebSocket connected; subscription requested for %s", settings.twelve_data_symbol)
                    delay = 2
                    while True:
                        event = json.loads(await ws.recv())
                        if event.get("event") != "price":
                            if event.get("status") == "error":
                                log.error("Provider subscription error: %s", event)
                            continue
                        value = event.get("price")
                        if value is None:
                            continue
                        stamp = event.get("timestamp")
                        when = (datetime.fromtimestamp(float(stamp), tz=timezone.utc)
                                if stamp is not None else datetime.now(timezone.utc))
                        await post(client, base, settings.ingest_api_key, "ticks/batch", {
                            "ticks": [{"symbol": symbol, "event_time": when.isoformat(),
                                       "price": str(value), "source": "twelvedata"}]})
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("Feed disconnected; retrying in %.1fs", delay)
                await asyncio.sleep(delay + random.random())
                delay = min(delay * 2, 60)

if __name__ == "__main__":
    asyncio.run(run())
