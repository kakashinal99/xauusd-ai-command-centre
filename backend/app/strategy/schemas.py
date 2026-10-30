"""Configuration for the baseline signal generator."""

from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class DonchianAtrConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    lookback: int = Field(default=20, ge=2, le=500)
    atr_period: int = Field(default=14, ge=2, le=200)
    atr_stop_multiple: Decimal = Field(default=Decimal("2"), gt=0, le=Decimal("10"))
    reward_risk_ratio: Decimal = Field(default=Decimal("2"), gt=0, le=Decimal("10"))
