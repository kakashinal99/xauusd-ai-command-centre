"""FastAPI application entry point."""

from fastapi import FastAPI

from app.backtesting.engine import run_backtest
from app.backtesting.schemas import BacktestConfig, BacktestRequest, BacktestResult
from app.config import get_settings
from app.strategy.donchian_atr import generate_donchian_atr_signals
from app.strategy.schemas import StrategyBacktestRequest

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Backend foundation for a demo-first XAUUSD trading research platform.",
)


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {"name": settings.app_name, "status": "online", "environment": settings.app_env}


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(f"{settings.api_v1_prefix}/status", tags=["system"])
def api_status() -> dict[str, str]:
    return {
        "status": "ok",
        "environment": settings.app_env,
        "trading_mode": "disabled",
        "broker": "ctrader",
        "market": "XAUUSD",
    }


@app.post(f"{settings.api_v1_prefix}/research/backtest/donchian-atr", response_model=BacktestResult, tags=["research"])
def backtest_donchian_atr(payload: StrategyBacktestRequest) -> BacktestResult:
    """Run a research-only baseline strategy backtest. This endpoint cannot trade."""
    signals = generate_donchian_atr_signals(payload.candles, payload.strategy)
    config = BacktestConfig(
        initial_equity=payload.initial_equity,
        risk_per_trade_pct=payload.risk_per_trade_pct,
        spread=payload.spread,
        slippage_per_side=payload.slippage_per_side,
        commission_per_unit_round_trip=payload.commission_per_unit_round_trip,
    )
    request = BacktestRequest(candles=payload.candles, signals=signals, config=config)
    return run_backtest(request)
