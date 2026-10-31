"""API schema for side-by-side strategy research."""
from decimal import Decimal
from pydantic import BaseModel, Field

from app.market_data.schemas import CandleInput
from app.strategy.schemas import BreakoutRetestConfig, DonchianAtrConfig, DowCandlestickConfig, RsiMeanReversionConfig


class StrategyComparisonRequest(BaseModel):
    candles: list[CandleInput] = Field(min_length=2)
    initial_equity: Decimal = Field(default=Decimal("10000"), gt=0)
    risk_per_trade_pct: Decimal = Field(default=Decimal("0.25"), gt=0, le=Decimal("1"))
    spread: Decimal = Field(default=Decimal("0"), ge=0)
    slippage_per_side: Decimal = Field(default=Decimal("0"), ge=0)
    commission_per_unit_round_trip: Decimal = Field(default=Decimal("0"), ge=0)
    donchian: DonchianAtrConfig = DonchianAtrConfig()
    dow_candlestick: DowCandlestickConfig = DowCandlestickConfig()
    rsi_mean_reversion: RsiMeanReversionConfig = RsiMeanReversionConfig()
    breakout_retest: BreakoutRetestConfig = BreakoutRetestConfig()
