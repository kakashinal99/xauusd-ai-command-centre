"""Run all registered research strategies and attribute results by market regime.

Regimes are heuristic labels, not predictions. They are calculated using only
completed candles available at each signal timestamp.
"""
from decimal import Decimal

from app.backtesting.engine import run_backtest
from app.backtesting.schemas import BacktestConfig, BacktestRequest
from app.market_data.schemas import CandleInput
from app.strategy.breakout_retest import generate_breakout_retest_signals
from app.strategy.donchian_atr import generate_donchian_atr_signals
from app.strategy.dow_candlestick import generate_dow_candlestick_signals
from app.strategy.rsi_mean_reversion import generate_rsi_mean_reversion_signals
from app.strategy.schemas import BreakoutRetestConfig, DonchianAtrConfig, DowCandlestickConfig, RsiMeanReversionConfig

REGIMES = ("trending", "ranging", "high_volatility", "transition")


def classify_market_regimes(
    candles: list[CandleInput], lookback: int = 20, volatility_window: int = 100
) -> dict:
    """Classify each candle using rolling efficiency ratio and normalized range.

    High volatility takes precedence; otherwise efficiency ratio separates
    directional/trending from low-directionality/ranging conditions.
    """
    result = {}
    normalized_ranges = []
    for i, candle in enumerate(candles):
        true_range = candle.high - candle.low
        normalized = true_range / candle.close
        normalized_ranges.append(normalized)
        if i < lookback or i < 2:
            result[candle.open_time] = "transition"
            continue

        window = candles[i - lookback:i + 1]
        displacement = abs(window[-1].close - window[0].close)
        path = sum((abs(window[j].close - window[j - 1].close)
                    for j in range(1, len(window))), Decimal("0"))
        efficiency = displacement / path if path > 0 else Decimal("0")

        start = max(0, i - volatility_window + 1)
        sample = sorted(normalized_ranges[start:i + 1])
        # Require a minimally useful reference sample before assigning volatility.
        high_vol = False
        if len(sample) >= min(30, volatility_window):
            threshold = sample[min(len(sample) - 1, int((len(sample) - 1) * 0.8))]
            high_vol = normalized >= threshold and normalized > 0

        if high_vol:
            regime = "high_volatility"
        elif efficiency >= Decimal("0.35"):
            regime = "trending"
        elif efficiency <= Decimal("0.20"):
            regime = "ranging"
        else:
            regime = "transition"
        result[candle.open_time] = regime
    return result


def _run(candles, signals, config):
    request = BacktestRequest(candles=candles, signals=signals, config=config)
    return run_backtest(request)


def compare_strategies(
    candles: list[CandleInput],
    initial_equity: Decimal = Decimal("10000"),
    risk_per_trade_pct: Decimal = Decimal("0.25"),
    spread: Decimal = Decimal("0"),
    slippage_per_side: Decimal = Decimal("0"),
    commission_per_unit_round_trip: Decimal = Decimal("0"),
    donchian_config: DonchianAtrConfig | None = None,
    dow_config: DowCandlestickConfig | None = None,
    rsi_config: RsiMeanReversionConfig | None = None,
    breakout_retest_config: BreakoutRetestConfig | None = None,
) -> dict:
    if len(candles) < 2:
        raise ValueError("At least two candles are required")
    times = [c.open_time for c in candles]
    if times != sorted(times) or len(set(times)) != len(times):
        raise ValueError("Candles must be unique and chronological")

    config = BacktestConfig(
        initial_equity=initial_equity,
        risk_per_trade_pct=risk_per_trade_pct,
        spread=spread,
        slippage_per_side=slippage_per_side,
        commission_per_unit_round_trip=commission_per_unit_round_trip,
    )
    regimes = classify_market_regimes(candles)
    registry = {
        "donchian_atr": generate_donchian_atr_signals(candles, donchian_config),
        "dow_candlestick": generate_dow_candlestick_signals(candles, dow_config),
        "rsi_mean_reversion": generate_rsi_mean_reversion_signals(candles, rsi_config),
        "breakout_retest": generate_breakout_retest_signals(candles, breakout_retest_config),
    }
    comparison = {}
    for name, signals in registry.items():
        overall = _run(candles, signals, config)
        by_regime = {}
        for regime in REGIMES:
            # Filter signals by the regime known at the signal candle close.
            subset = [s for s in signals if regimes.get(s.signal_time) == regime]
            result = _run(candles, subset, config)
            by_regime[regime] = {
                "signal_count": len(subset),
                "trade_count": result.trade_count,
                "return_pct": result.return_pct,
                "profit_factor": result.profit_factor,
                "expectancy_per_trade": result.expectancy_per_trade,
                "win_rate_pct": result.win_rate_pct,
                "max_drawdown_pct": result.max_drawdown_pct,
            }
        comparison[name] = {
            "signal_count": len(signals),
            "overall": overall,
            "by_regime": by_regime,
        }

    return {
        "symbol": "XAUUSD",
        "candle_count": len(candles),
        "regime_method": {
            "name": "rolling_efficiency_ratio_and_normalized_range",
            "lookback": 20,
            "volatility_window": 100,
            "note": "Heuristic classification; validate thresholds out-of-sample.",
        },
        "regime_counts": {
            regime: sum(value == regime for value in regimes.values())
            for regime in REGIMES
        },
        "strategies": comparison,
        "selection_policy": {
            "automatic_switching": False,
            "reason": "Performance attribution is research-only; no strategy is selected or traded automatically.",
        },
    }
