"""Typed contracts for reproducible XAUUSD backtests."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.market_data.schemas import CandleInput


class TradeSignal(BaseModel):
    """Signal emitted after a candle closes; entry occurs at the next candle open."""
    model_config = ConfigDict(frozen=True)
    signal_time: datetime
    direction: Literal["long", "short"]
    stop_loss: Decimal = Field(gt=0)
    take_profit: Decimal = Field(gt=0)


class BacktestConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    initial_equity: Decimal = Field(default=Decimal("10000"), gt=0)
    risk_per_trade_pct: Decimal = Field(default=Decimal("0.25"), gt=0, le=Decimal("1"))
    spread: Decimal = Field(default=Decimal("0"), ge=0)
    slippage_per_side: Decimal = Field(default=Decimal("0"), ge=0)
    commission_per_unit_round_trip: Decimal = Field(default=Decimal("0"), ge=0)


class BacktestTrade(BaseModel):
    direction: Literal["long", "short"]
    signal_time: datetime
    entry_time: datetime
    exit_time: datetime
    entry_price: Decimal
    exit_price: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    quantity: Decimal
    gross_pnl: Decimal
    costs: Decimal
    net_pnl: Decimal
    exit_reason: Literal["stop_loss", "take_profit", "end_of_data"]


class BacktestResult(BaseModel):
    symbol: str = "XAUUSD"
    initial_equity: Decimal
    final_equity: Decimal
    net_profit: Decimal
    return_pct: Decimal
    trade_count: int
    wins: int
    losses: int
    win_rate_pct: Decimal
    gross_profit: Decimal
    gross_loss: Decimal
    profit_factor: Decimal | None
    expectancy_per_trade: Decimal
    max_drawdown_pct: Decimal
    trades: list[BacktestTrade]
    equity_curve: list[Decimal]


class BacktestRequest(BaseModel):
    """In-memory request contract; strategy generation is intentionally separate."""
    candles: list[CandleInput]
    signals: list[TradeSignal]
    config: BacktestConfig = BacktestConfig()

    @model_validator(mode="after")
    def validate_inputs(self):
        if len(self.candles) < 2:
            raise ValueError("At least two candles are required")
        times = [c.open_time for c in self.candles]
        if times != sorted(times) or len(set(times)) != len(times):
            raise ValueError("Candles must be unique and chronological")
        candle_times = set(times)
        if any(s.signal_time not in candle_times for s in self.signals):
            raise ValueError("Every signal_time must match a candle open_time")
        if len({s.signal_time for s in self.signals}) != len(self.signals):
            raise ValueError("Only one signal per candle is supported")
        for signal in self.signals:
            if signal.direction == "long" and signal.take_profit <= signal.stop_loss:
                raise ValueError("Long take_profit must be above stop_loss")
            if signal.direction == "short" and signal.take_profit >= signal.stop_loss:
                raise ValueError("Short take_profit must be below stop_loss")
        return self
