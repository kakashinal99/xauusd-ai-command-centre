from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.backtesting.engine import run_backtest
from app.backtesting.schemas import BacktestConfig, BacktestRequest, TradeSignal
from app.market_data.schemas import CandleInput


def candle(minute, o, h, l, c):
    return CandleInput(
        timeframe="M1",
        open_time=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=minute),
        open=Decimal(str(o)), high=Decimal(str(h)), low=Decimal(str(l)), close=Decimal(str(c)),
    )


def test_long_trade_enters_next_open_and_hits_target():
    candles = [candle(0, 100, 101, 99, 100), candle(1, 100, 106, 99, 105), candle(2, 105, 106, 104, 105)]
    signal = TradeSignal(signal_time=candles[0].open_time, direction="long", stop_loss=Decimal("95"), take_profit=Decimal("105"))
    result = run_backtest(BacktestRequest(candles=candles, signals=[signal]))
    assert result.trade_count == 1
    assert result.trades[0].entry_time == candles[1].open_time
    assert result.trades[0].exit_reason == "take_profit"
    assert result.final_equity > result.initial_equity


def test_stop_wins_if_stop_and_target_touched_in_same_bar():
    candles = [candle(0, 100, 101, 99, 100), candle(1, 100, 106, 94, 100), candle(2, 100, 101, 99, 100)]
    signal = TradeSignal(signal_time=candles[0].open_time, direction="long", stop_loss=Decimal("95"), take_profit=Decimal("105"))
    result = run_backtest(BacktestRequest(candles=candles, signals=[signal]))
    assert result.trades[0].exit_reason == "stop_loss"
    assert result.final_equity < result.initial_equity


def test_spread_and_slippage_reduce_long_profit():
    candles = [candle(0, 100, 101, 99, 100), candle(1, 100, 106, 99, 105), candle(2, 105, 106, 104, 105)]
    signal = TradeSignal(signal_time=candles[0].open_time, direction="long", stop_loss=Decimal("95"), take_profit=Decimal("105"))
    free = run_backtest(BacktestRequest(candles=candles, signals=[signal]))
    costly = run_backtest(BacktestRequest(candles=candles, signals=[signal], config=BacktestConfig(spread=Decimal("0.2"), slippage_per_side=Decimal("0.1"))))
    assert costly.final_equity < free.final_equity


def test_rejects_unsorted_candles():
    candles = [candle(1, 100, 101, 99, 100), candle(0, 100, 101, 99, 100)]
    with pytest.raises(ValueError):
        BacktestRequest(candles=candles, signals=[])


def test_market_data_contract_restricts_symbol_to_xauusd():
    with pytest.raises(ValueError):
        CandleInput(symbol="EURUSD", timeframe="M1", open_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
                    open=Decimal("100"), high=Decimal("101"), low=Decimal("99"), close=Decimal("100"))
