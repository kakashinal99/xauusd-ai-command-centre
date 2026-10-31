"""Persistent market-data API. Broker-neutral; cTrader is intentionally not connected."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db_session, get_engine
from app.models import Base, Candle, MarketTick
from app.market_data.schemas import CandleInput, normalize_candles

router = APIRouter(prefix="/market-data", tags=["market-data"])
settings = get_settings()


async def require_ingest_key(x_ingest_key: str | None = Header(default=None)):
    if not settings.ingest_api_key:
        raise HTTPException(status_code=503, detail="Ingestion is disabled until INGEST_API_KEY is configured")
    import secrets
    if x_ingest_key is None or not secrets.compare_digest(x_ingest_key, settings.ingest_api_key):
        raise HTTPException(status_code=401, detail="Invalid ingestion key")


class CandleBatch(BaseModel):
    candles: list[CandleInput] = Field(min_length=1, max_length=5000)


class TickInput(BaseModel):
    model_config = ConfigDict(frozen=True)
    symbol: Literal["XAUUSD"] = "XAUUSD"
    event_time: datetime
    bid: Decimal | None = None
    ask: Decimal | None = None
    source: str = "manual"

    @field_validator("event_time")
    @classmethod
    def validate_event_time(cls, value: datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("event_time must include a timezone")
        return value.astimezone(timezone.utc)


class TickBatch(BaseModel):
    ticks: list[TickInput] = Field(min_length=1, max_length=10000)


async def initialize_storage() -> None:
    """Create baseline tables when DATABASE_URL is configured."""
    engine = get_engine()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


@router.post("/candles/batch", dependencies=[Depends(require_ingest_key)])
async def ingest_candles(payload: CandleBatch, session: AsyncSession = Depends(get_db_session)):
    candles = normalize_candles(payload.candles)
    rows = [{
        "symbol": c.symbol, "timeframe": c.timeframe, "open_time": c.open_time,
        "open": c.open, "high": c.high, "low": c.low, "close": c.close,
        "volume": c.volume, "source": c.source, "created_at": datetime.now(timezone.utc),
    } for c in candles]
    statement = insert(Candle).values(rows)
    statement = statement.on_conflict_do_update(
        constraint="uq_candle_symbol_tf_open",
        set_={key: getattr(statement.excluded, key) for key in
              ("open", "high", "low", "close", "volume", "source", "created_at")},
    )
    await session.execute(statement)
    await session.commit()
    return {"stored": len(rows), "symbol": "XAUUSD", "status": "persisted"}


@router.post("/ticks/batch", dependencies=[Depends(require_ingest_key)])
async def ingest_ticks(payload: TickBatch, session: AsyncSession = Depends(get_db_session)):
    rows = []
    for tick in payload.ticks:
        if tick.event_time.tzinfo is None or tick.event_time.utcoffset() is None:
            raise HTTPException(status_code=422, detail="event_time must include a timezone")
        if tick.bid is None and tick.ask is None:
            raise HTTPException(status_code=422, detail="Each tick needs bid or ask")
        if tick.bid is not None and tick.bid <= 0 or tick.ask is not None and tick.ask <= 0:
            raise HTTPException(status_code=422, detail="Prices must be positive")
        if tick.bid is not None and tick.ask is not None and tick.ask < tick.bid:
            raise HTTPException(status_code=422, detail="ask cannot be below bid")
        rows.append({"symbol": tick.symbol, "event_time": tick.event_time.astimezone(timezone.utc),
                     "bid": tick.bid, "ask": tick.ask, "source": tick.source})
    await session.execute(insert(MarketTick).values(rows))
    await session.commit()
    return {"stored": len(rows), "symbol": "XAUUSD", "status": "persisted"}


@router.get("/summary")
async def market_data_summary(session: AsyncSession = Depends(get_db_session)):
    candle_count = await session.scalar(select(func.count()).select_from(Candle))
    tick_count = await session.scalar(select(func.count()).select_from(MarketTick))
    latest_candle = await session.scalar(select(func.max(Candle.open_time)))
    latest_tick = await session.scalar(select(func.max(MarketTick.event_time)))
    return {
        "symbol": "XAUUSD", "candles": candle_count or 0, "ticks": tick_count or 0,
        "latest_candle": latest_candle, "latest_tick": latest_tick,
        "source_connected": False, "trading_enabled": False,
    }


@router.get("/candles")
async def get_candles(timeframe: str = Query("M1", max_length=12),
                      limit: int = Query(500, ge=1, le=5000),
                      session: AsyncSession = Depends(get_db_session)):
    result = await session.scalars(
        select(Candle).where(Candle.symbol == "XAUUSD", Candle.timeframe == timeframe)
        .order_by(Candle.open_time.desc()).limit(limit)
    )
    return list(reversed(result.all()))
