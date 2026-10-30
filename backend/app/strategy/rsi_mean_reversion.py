"""RSI mean-reversion signal generator. Research only; no broker execution."""
from decimal import Decimal

from app.backtesting.schemas import TradeSignal
from app.market_data.schemas import CandleInput
from app.strategy.indicators import simple_atr
from app.strategy.schemas import RsiMeanReversionConfig

ZERO = Decimal("0")
HUNDRED = Decimal("100")


def simple_rsi(candles: list[CandleInput], period: int) -> list[Decimal | None]:
    """Simple rolling RSI; intentionally not Wilder-smoothed."""
    output: list[Decimal | None] = [None] * len(candles)
    changes = [candles[i].close - candles[i - 1].close for i in range(1, len(candles))]
    for i in range(period, len(candles)):
        window = changes[i - period:i]
        gains = sum((max(change, ZERO) for change in window), ZERO)
        losses = sum((max(-change, ZERO) for change in window), ZERO)
        if losses == ZERO:
            output[i] = HUNDRED if gains > ZERO else Decimal("50")
        else:
            relative_strength = gains / losses
            output[i] = HUNDRED - HUNDRED / (Decimal("1") + relative_strength)
    return output


def generate_rsi_mean_reversion_signals(
    candles: list[CandleInput], config: RsiMeanReversionConfig | None = None
) -> list[TradeSignal]:
    config = config or RsiMeanReversionConfig()
    rsi = simple_rsi(candles, config.rsi_period)
    atr = simple_atr(candles, config.atr_period)
    signals: list[TradeSignal] = []
    for i in range(1, len(candles)):
        previous, current, volatility = rsi[i - 1], rsi[i], atr[i]
        if previous is None or current is None or volatility is None or volatility <= ZERO:
            continue
        direction = None
        if previous <= config.oversold and current > config.oversold:
            direction = "long"
        elif previous >= config.overbought and current < config.overbought:
            direction = "short"
        if direction is None:
            continue

        distance = volatility * config.atr_stop_multiple
        close = candles[i].close
        if direction == "long":
            stop, target = close - distance, close + distance * config.reward_risk_ratio
            if stop <= ZERO:
                continue
        else:
            stop, target = close + distance, close - distance * config.reward_risk_ratio
            if target <= ZERO:
                continue
        signals.append(TradeSignal(
            signal_time=candles[i].open_time,
            direction=direction,
            stop_loss=stop,
            take_profit=target,
        ))
    return signals
