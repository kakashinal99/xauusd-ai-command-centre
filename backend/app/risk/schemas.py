"""Typed inputs and outputs for deterministic trade risk checks."""

from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class RiskLimits(BaseModel):
    model_config = ConfigDict(frozen=True)

    max_risk_per_trade_pct: Decimal = Field(default=Decimal("0.25"), gt=0, le=Decimal("1"))
    max_daily_loss_pct: Decimal = Field(default=Decimal("2.0"), gt=0, le=Decimal("10"))
    max_weekly_loss_pct: Decimal = Field(default=Decimal("4.0"), gt=0, le=Decimal("20"))
    max_drawdown_pct: Decimal = Field(default=Decimal("6.0"), gt=0, le=Decimal("30"))
    max_open_positions: int = Field(default=1, ge=1, le=10)


class RiskCheckRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    equity: Decimal = Field(gt=0)
    day_start_equity: Decimal = Field(gt=0)
    week_start_equity: Decimal = Field(gt=0)
    peak_equity: Decimal = Field(gt=0)
    requested_risk_pct: Decimal = Field(gt=0)
    open_positions: int = Field(default=0, ge=0)
    has_stop_loss: bool
    kill_switch_active: bool = False
    trading_enabled: bool = False

    @model_validator(mode="after")
    def validate_equity_references(self):
        if self.day_start_equity <= 0 or self.week_start_equity <= 0 or self.peak_equity <= 0:
            raise ValueError("Equity reference values must be positive")
        return self


class RiskCheckResponse(BaseModel):
    allowed: bool
    reasons: list[str]
    current_daily_loss_pct: Decimal
    current_weekly_loss_pct: Decimal
    current_drawdown_pct: Decimal
    approved_risk_pct: Decimal
    max_risk_amount: Decimal
