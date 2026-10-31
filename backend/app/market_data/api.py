"""Persistent market-data API. Provider-neutral; no broker execution is exposed."""
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.database import get_db_session, get_engine
from app.models import Base, Candle, MarketTick
from app.market_data.schemas import CandleInput, canonical_symbol, normalize_candles

router = APIRouter(prefix="/market-data", tags=["market-data"])
settings = get_settings()

def configured_symbol() -> str:
    return canonical_symbol(settings.twelve_data_symbol)

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
    symbol: str = "XAUUSD"
    event_time: datetime
    price: Decimal | None = None
    bid: Decimal | None = None
    ask: Decimal | None = None
    source: str = "manual"

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str):
        return canonical_symbol(value)

    @field_validator("event_time")
    @classmethod
    def validate_event_time(cls, value: datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("event_time must include a timezone")
        return value.astimezone(timezone.utc)

class TickBatch(BaseModel):
    ticks: list[TickInput] = Field(min_length=1, max_length=10000)

async def initialize_storage() -> None:
    engine = get_engine()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.execute(text("ALTER TABLE market_ticks ADD COLUMN IF NOT EXISTS price NUMERIC(18, 8) NULL"))

@router.post("/candles/batch", dependencies=[Depends(require_ingest_key)])
async def ingest_candles(payload: CandleBatch, session: AsyncSession = Depends(get_db_session)):
    candles = normalize_candles(payload.candles)
    rows = [{"symbol": c.symbol, "timeframe": c.timeframe, "open_time": c.open_time, "open": c.open,
             "high": c.high, "low": c.low, "close": c.close, "volume": c.volume, "source": c.source,
             "created_at": datetime.now(timezone.utc)} for c in candles]
    statement = insert(Candle).values(rows)
    statement = statement.on_conflict_do_update(
        constraint="uq_candle_symbol_tf_open",
        set_={key: getattr(statement.excluded, key) for key in
              ("open", "high", "low", "close", "volume", "source", "created_at")})
    await session.execute(statement)
    await session.commit()
    symbols = sorted({c.symbol for c in candles})
    return {"stored": len(rows), "symbols": symbols, "status": "persisted"}

@router.post("/ticks/batch", dependencies=[Depends(require_ingest_key)])
async def ingest_ticks(payload: TickBatch, session: AsyncSession = Depends(get_db_session)):
    rows = []
    for tick in payload.ticks:
        if tick.price is None and tick.bid is None and tick.ask is None:
            raise HTTPException(status_code=422, detail="Each tick needs price, bid or ask")
        if any(value is not None and value <= 0 for value in (tick.price, tick.bid, tick.ask)):
            raise HTTPException(status_code=422, detail="Prices must be positive")
        if tick.bid is not None and tick.ask is not None and tick.ask < tick.bid:
            raise HTTPException(status_code=422, detail="ask cannot be below bid")
        rows.append({"symbol": tick.symbol, "event_time": tick.event_time, "price": tick.price,
                     "bid": tick.bid, "ask": tick.ask, "source": tick.source})
    await session.execute(insert(MarketTick).values(rows))
    await session.commit()
    return {"stored": len(rows), "symbols": sorted({t.symbol for t in payload.ticks}), "status": "persisted"}

@router.get("/summary")
async def market_data_summary(session: AsyncSession = Depends(get_db_session)):
    symbol = configured_symbol()
    candle_filter = Candle.symbol == symbol
    tick_filter = MarketTick.symbol == symbol
    candle_count = await session.scalar(select(func.count()).select_from(Candle).where(candle_filter))
    tick_count = await session.scalar(select(func.count()).select_from(MarketTick).where(tick_filter))
    latest_candle = await session.scalar(select(func.max(Candle.open_time)).where(candle_filter))
    latest_tick = await session.scalar(select(func.max(MarketTick.event_time)).where(tick_filter))
    return {"symbol": symbol, "candles": candle_count or 0, "ticks": tick_count or 0,
            "latest_candle": latest_candle, "latest_tick": latest_tick,
            "source_connected": False, "trading_enabled": False}

@router.get("/candles")
async def get_candles(timeframe: str = Query("M1", max_length=12),
                      limit: int = Query(500, ge=1, le=5000),
                      session: AsyncSession = Depends(get_db_session)):
    result = await session.scalars(
        select(Candle).where(Candle.symbol == configured_symbol(), Candle.timeframe == timeframe)
        .order_by(Candle.open_time.desc()).limit(limit))
    return list(reversed(result.all()))
