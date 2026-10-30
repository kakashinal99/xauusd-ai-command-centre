"""Deterministic OHLC backtester. No broker connectivity or order execution."""

from decimal import Decimal

from app.backtesting.schemas import BacktestConfig, BacktestRequest, BacktestResult, BacktestTrade, TradeSignal

ZERO = Decimal("0")
ONE = Decimal("1")
HUNDRED = Decimal("100")


def _execution_price(raw_price: Decimal, direction: str, is_entry: bool, config: BacktestConfig) -> Decimal:
    friction = config.spread / Decimal("2") + config.slippage_per_side
    adverse = friction if (direction == "long") == is_entry else -friction
    return raw_price + adverse


def _exit_for_candle(signal: TradeSignal, candle):
    """Return raw exit and reason; if both levels are touched, stop wins."""
    if signal.direction == "long":
        if candle.open <= signal.stop_loss:
            return candle.open, "stop_loss"
        if candle.open >= signal.take_profit:
            return signal.take_profit, "take_profit"
        stop_hit, target_hit = candle.low <= signal.stop_loss, candle.high >= signal.take_profit
    else:
        if candle.open >= signal.stop_loss:
            return candle.open, "stop_loss"
        if candle.open <= signal.take_profit:
            return signal.take_profit, "take_profit"
        stop_hit, target_hit = candle.high >= signal.stop_loss, candle.low <= signal.take_profit
    if stop_hit:
        return signal.stop_loss, "stop_loss"
    if target_hit:
        return signal.take_profit, "take_profit"
    return None


def run_backtest(request: BacktestRequest) -> BacktestResult:
    """Run one-position-at-a-time backtest with next-bar-open entries.

    Quantity is abstract XAUUSD units: risk cash / price distance. Broker lot
    sizing and account-currency conversion must be supplied separately.
    """
    candles, config = request.candles, request.config
    signals = {s.signal_time: s for s in request.signals}
    equity = config.initial_equity
    peak = equity
    max_drawdown = ZERO
    curve = [equity]
    trades: list[BacktestTrade] = []
    i = 0
    while i < len(candles) - 1:
        signal = signals.get(candles[i].open_time)
        if signal is None:
            i += 1
            continue
        entry_candle = candles[i + 1]
        entry_price = _execution_price(entry_candle.open, signal.direction, True, config)
        stop_distance = abs(entry_price - signal.stop_loss)
        if stop_distance <= ZERO:
            i += 1
            continue
        risk_cash = equity * config.risk_per_trade_pct / HUNDRED
        quantity = risk_cash / stop_distance
        exit_index, raw_exit, reason = len(candles) - 1, candles[-1].close, "end_of_data"
        for j in range(i + 1, len(candles)):
            hit = _exit_for_candle(signal, candles[j])
            if hit is not None:
                raw_exit, reason = hit
                exit_index = j
                break
        exit_candle = candles[exit_index]
        exit_price = _execution_price(raw_exit, signal.direction, False, config)
        sign = ONE if signal.direction == "long" else Decimal("-1")
        gross = (exit_price - entry_price) * quantity * sign
        costs = config.commission_per_unit_round_trip * quantity
        net = gross - costs
        equity += net
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, (peak - equity) / peak * HUNDRED)
        curve.append(equity)
        trades.append(BacktestTrade(
            direction=signal.direction, signal_time=signal.signal_time,
            entry_time=entry_candle.open_time, exit_time=exit_candle.open_time,
            entry_price=entry_price, exit_price=exit_price,
            stop_loss=signal.stop_loss, take_profit=signal.take_profit,
            quantity=quantity, gross_pnl=gross, costs=costs, net_pnl=net,
            exit_reason=reason,
        ))
        i = exit_index + 1

    wins = sum(t.net_pnl > ZERO for t in trades)
    losses = sum(t.net_pnl < ZERO for t in trades)
    gross_profit = sum((t.net_pnl for t in trades if t.net_pnl > ZERO), ZERO)
    gross_loss = abs(sum((t.net_pnl for t in trades if t.net_pnl < ZERO), ZERO))
    count = len(trades)
    # None means undefined (no losing trades or no trades), not an infinite numeric value.
    profit_factor = gross_profit / gross_loss if gross_loss > ZERO else None
    net_profit = equity - config.initial_equity
    return BacktestResult(
        initial_equity=config.initial_equity, final_equity=equity,
        net_profit=net_profit, return_pct=net_profit / config.initial_equity * HUNDRED,
        trade_count=count, wins=wins, losses=losses,
        win_rate_pct=Decimal(wins) / Decimal(count) * HUNDRED if count else ZERO,
        gross_profit=gross_profit, gross_loss=gross_loss, profit_factor=profit_factor,
        expectancy_per_trade=net_profit / Decimal(count) if count else ZERO,
        max_drawdown_pct=max_drawdown, trades=trades, equity_curve=curve,
    )
