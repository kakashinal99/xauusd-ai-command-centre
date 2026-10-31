from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.market_data.schemas import CandleInput
from app.research.comparison import REGIMES, classify_market_regimes, compare_strategies


def make_candles(count=160):
    rows = []
    price = Decimal("2300")
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    for i in range(count):
        # Deterministic alternating drift creates enough history for both engines.
        drift = Decimal("1.2") if (i // 35) % 2 == 0 else Decimal("-0.8")
        open_price = price
        close = price + drift + (Decimal("0.4") if i % 3 == 0 else Decimal("-0.2"))
        high = max(open_price, close) + Decimal("1.5")
        low = min(open_price, close) - Decimal("1.5")
        rows.append(CandleInput(
            timeframe="M15", open_time=start + timedelta(minutes=15 * i),
            open=open_price, high=high, low=low, close=close,
        ))
        price = close
    return rows


def test_regime_classifier_labels_every_candle():
    candles = make_candles()
    regimes = classify_market_regimes(candles)
    assert len(regimes) == len(candles)
    assert set(regimes.values()).issubset(set(REGIMES))
    assert list(regimes.values())[:20] == ["transition"] * 20


def test_comparison_returns_all_registered_strategies_and_regimes():
    result = compare_strategies(make_candles())
    assert set(result["strategies"]) == {"donchian_atr", "dow_candlestick", "rsi_mean_reversion", "breakout_retest"}
    for strategy in result["strategies"].values():
        assert set(strategy["by_regime"]) == set(REGIMES)
        assert "overall" in strategy
        assert "trade_count" in strategy["overall"]
    assert result["selection_policy"]["automatic_switching"] is False


def test_comparison_rejects_non_chronological_candles():
    candles = make_candles(50)
    candles[2], candles[3] = candles[3], candles[2]
    try:
        compare_strategies(candles)
    except ValueError as exc:
        assert "chronological" in str(exc)
    else:
        raise AssertionError("Expected chronological validation")
