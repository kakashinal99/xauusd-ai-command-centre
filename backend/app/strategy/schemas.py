"""Configuration for the baseline signal generator."""

from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class DonchianAtrConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    lookback: int = Field(default=20, ge=2, le=500)
    atr_period: int = Field(default=14, ge=2, le=200)
    atr_stop_multiple: Decimal = Field(default=Decimal("2"), gt=0, le=Decimal("10"))
    reward_risk_ratio: Decimal = Field(default=Decimal("2"), gt=0, le=Decimal("10"))


class StrategyBacktestRequest(BaseModel):
    """API payload for running the baseline strategy through the backtester."""
    candles: list = Field(min_length=2)
    strategy: DonchianAtrConfig = DonchianAtrConfig()
    initial_equity: Decimal = Field(default=Decimal("10000"), gt=0)
    risk_per_trade_pct: Decimal = Field(default=Decimal("0.25"), gt=0, le=Decimal("1"))
    spread: Decimal = Field(default=Decimal("0"), ge=0)
    slippage_per_side: Decimal = Field(default=Decimal("0"), ge=0)
    commission_per_unit_round_trip: Decimal = Field(default=Decimal("0"), ge=0)
