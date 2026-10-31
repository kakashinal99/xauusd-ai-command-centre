"""Configuration for the baseline signal generator."""

from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

from app.market_data.schemas import CandleInput


class DonchianAtrConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    lookback: int = Field(default=20, ge=2, le=500)
    atr_period: int = Field(default=14, ge=2, le=200)
    atr_stop_multiple: Decimal = Field(default=Decimal("2"), gt=0, le=Decimal("10"))
    reward_risk_ratio: Decimal = Field(default=Decimal("2"), gt=0, le=Decimal("10"))


class StrategyBacktestRequest(BaseModel):
    """API payload for running the baseline strategy through the backtester."""
    candles: list[CandleInput] = Field(min_length=2)
    strategy: DonchianAtrConfig = DonchianAtrConfig()
    initial_equity: Decimal = Field(default=Decimal("10000"), gt=0)
    risk_per_trade_pct: Decimal = Field(default=Decimal("0.25"), gt=0, le=Decimal("1"))
    spread: Decimal = Field(default=Decimal("0"), ge=0)
    slippage_per_side: Decimal = Field(default=Decimal("0"), ge=0)
    commission_per_unit_round_trip: Decimal = Field(default=Decimal("0"), ge=0)


 
class RsiMeanReversionConfig(BaseModel):
    """RSI threshold-recovery mean-reversion settings."""
    model_config = ConfigDict(frozen=True)
    rsi_period: int = Field(default=14, ge=2, le=200)
    atr_period: int = Field(default=14, ge=2, le=200)
    oversold: Decimal = Field(default=Decimal("30"), ge=0, lt=Decimal("50"))
    overbought: Decimal = Field(default=Decimal("70"), gt=Decimal("50"), le=100)
    atr_stop_multiple: Decimal = Field(default=Decimal("1.5"), gt=0, le=Decimal("10"))
    reward_risk_ratio: Decimal = Field(default=Decimal("1.5"), gt=0, le=Decimal("10"))


class DowCandlestickConfig(BaseModel):
    """Mechanical Dow structure and candle-confirmation settings."""
    model_config = ConfigDict(frozen=True)
    pivot_left: int = Field(default=3, ge=1, le=20)
    pivot_right: int = Field(default=3, ge=1, le=20)
    atr_period: int = Field(default=14, ge=2, le=200)
    stop_atr_buffer: Decimal = Field(default=Decimal("0.2"), ge=0, le=Decimal("5"))
    reward_risk_ratio: Decimal = Field(default=Decimal("2"), gt=0, le=Decimal("10"))
    wick_body_ratio: Decimal = Field(default=Decimal("2"), gt=0, le=Decimal("10"))


class DowStrategyBacktestRequest(BaseModel):
    """API payload for Dow Theory plus candlestick research backtest."""
    candles: list[CandleInput] = Field(min_length=2)
    strategy: DowCandlestickConfig = DowCandlestickConfig()
    initial_equity: Decimal = Field(default=Decimal("10000"), gt=0)
    risk_per_trade_pct: Decimal = Field(default=Decimal("0.25"), gt=0, le=Decimal("1"))
    spread: Decimal = Field(default=Decimal("0"), ge=0)
    slippage_per_side: Decimal = Field(default=Decimal("0"), ge=0)
    commission_per_unit_round_trip: Decimal = Field(default=Decimal("0"), ge=0)


class BreakoutRetestConfig(BaseModel):
    """Close-confirmed range breakout followed by a bounded retest."""
    model_config = ConfigDict(frozen=True)
    lookback: int = Field(default=20, ge=3, le=500)
    retest_window: int = Field(default=8, ge=1, le=100)
    atr_period: int = Field(default=14, ge=2, le=200)
    retest_tolerance_atr: Decimal = Field(default=Decimal("0.25"), ge=0, le=Decimal("2"))
    stop_atr_buffer: Decimal = Field(default=Decimal("0.2"), ge=0, le=Decimal("5"))
    reward_risk_ratio: Decimal = Field(default=Decimal("2"), gt=0, le=Decimal("10"))
