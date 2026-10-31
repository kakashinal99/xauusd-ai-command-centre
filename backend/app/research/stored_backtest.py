"""Database-backed research backtests over persisted OHLC candles."""
from datetime import datetime
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.backtesting.engine import run_backtest
from app.backtesting.schemas import BacktestConfig, BacktestRequest
from app.database import get_db_session
from app.market_data.schemas import CandleInput
from app.models import Candle
from app.strategy.donchian_atr import generate_donchian_atr_signals
from app.strategy.schemas import DonchianAtrConfig

router = APIRouter(prefix="/research", tags=["research"])


class StoredBacktestRequest(BaseModel):
    symbol: Literal["XAUUSD"] = "XAUUSD"
    timeframe: Literal["M1"] = "M1"
    limit: int = Field(default=10000, ge=100, le=50000)
    start_time: datetime | None = None
    end_time: datetime | None = None
    strategy: Literal["donchian_atr"] = "donchian_atr"
    donchian: DonchianAtrConfig = DonchianAtrConfig()
    initial_equity: Decimal = Field(default=Decimal("10000"), gt=0)
    risk_per_trade_pct: Decimal = Field(default=Decimal("0.25"), gt=0, le=Decimal("1"))
    spread: Decimal = Field(default=Decimal("0"), ge=0)
    slippage_per_side: Decimal = Field(default=Decimal("0"), ge=0)
    commission_per_unit_round_trip: Decimal = Field(default=Decimal("0"), ge=0)


@router.post("/backtest/stored")
async def backtest_stored_candles(
    payload: StoredBacktestRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """Run a research-only backtest using candles already stored in PostgreSQL."""
    if payload.start_time and payload.start_time.tzinfo is None:
        raise HTTPException(status_code=422, detail="start_time must include a timezone")
    if payload.end_time and payload.end_time.tzinfo is None:
        raise HTTPException(status_code=422, detail="end_time must include a timezone")
    if payload.start_time and payload.end_time and payload.start_time >= payload.end_time:
        raise HTTPException(status_code=422, detail="start_time must be earlier than end_time")

    filters = [Candle.symbol == payload.symbol, Candle.timeframe == payload.timeframe]
    if payload.start_time:
        filters.append(Candle.open_time >= payload.start_time)
    if payload.end_time:
        filters.append(Candle.open_time <= payload.end_time)

    count = await session.scalar(select(func.count()).select_from(Candle).where(*filters))
    rows = await session.scalars(
        select(Candle).where(*filters).order_by(Candle.open_time.desc()).limit(payload.limit)
    )
    stored = list(reversed(rows.all()))
    if len(stored) < 100:
        raise HTTPException(
            status_code=422,
            detail=f"At least 100 stored {payload.symbol} {payload.timeframe} candles are required; found {len(stored)}.",
        )

    candles = [
        CandleInput(
            symbol=row.symbol, timeframe=row.timeframe, open_time=row.open_time,
            open=row.open, high=row.high, low=row.low, close=row.close,
            volume=row.volume, source=row.source,
        )
        for row in stored
    ]
    signals = generate_donchian_atr_signals(candles, payload.donchian)
    config = BacktestConfig(
        initial_equity=payload.initial_equity,
        risk_per_trade_pct=payload.risk_per_trade_pct,
        spread=payload.spread,
        slippage_per_side=payload.slippage_per_side,
        commission_per_unit_round_trip=payload.commission_per_unit_round_trip,
    )
    result = run_backtest(BacktestRequest(candles=candles, signals=signals, config=config))
    return {
        "data_source": "postgresql",
        "symbol": payload.symbol,
        "timeframe": payload.timeframe,
        "candles_used": len(candles),
        "matching_candles_available": count or 0,
        "first_candle": candles[0].open_time,
        "last_candle": candles[-1].open_time,
        "strategy": payload.strategy,
        "strategy_parameters": payload.donchian.model_dump(mode="json"),
        "execution_model": "signal after candle close; entry at next candle open; stop wins if stop and target touch in same candle",
        "result": result.model_dump(mode="json"),
        "trading_enabled": False,
    }
