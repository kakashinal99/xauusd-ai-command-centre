"""Fail-closed risk evaluation. This module never submits orders."""

from decimal import Decimal

from app.risk.schemas import RiskCheckRequest, RiskCheckResponse, RiskLimits

ZERO = Decimal("0")
HUNDRED = Decimal("100")


def _loss_pct(reference_equity: Decimal, current_equity: Decimal) -> Decimal:
    """Return loss as a positive percentage; gains are represented as zero loss."""
    return max(ZERO, (reference_equity - current_equity) / reference_equity * HUNDRED)


def evaluate_risk(request: RiskCheckRequest, limits: RiskLimits | None = None) -> RiskCheckResponse:
    """Evaluate a proposed risk allocation against hard limits.

    The engine is deliberately fail-closed: trading must be explicitly enabled,
    a stop loss must exist, and all independent loss/position limits must pass.
    """
    limits = limits or RiskLimits()
    daily_loss = _loss_pct(request.day_start_equity, request.equity)
    weekly_loss = _loss_pct(request.week_start_equity, request.equity)
    drawdown = _loss_pct(request.peak_equity, request.equity)
    reasons: list[str] = []

    if not request.trading_enabled:
        reasons.append("Trading is disabled")
    if request.kill_switch_active:
        reasons.append("Kill switch is active")
    if not request.has_stop_loss:
        reasons.append("A stop loss is required")
    if request.requested_risk_pct > limits.max_risk_per_trade_pct:
        reasons.append("Requested risk exceeds the per-trade limit")
    if request.open_positions >= limits.max_open_positions:
        reasons.append("Maximum open positions reached")
    if daily_loss >= limits.max_daily_loss_pct:
        reasons.append("Daily loss limit reached")
    if weekly_loss >= limits.max_weekly_loss_pct:
        reasons.append("Weekly loss limit reached")
    if drawdown >= limits.max_drawdown_pct:
        reasons.append("Maximum drawdown limit reached")

    allowed = not reasons
    approved_risk = request.requested_risk_pct if allowed else ZERO
    risk_amount = request.equity * approved_risk / HUNDRED

    return RiskCheckResponse(
        allowed=allowed,
        reasons=reasons,
        current_daily_loss_pct=daily_loss,
        current_weekly_loss_pct=weekly_loss,
        current_drawdown_pct=drawdown,
        approved_risk_pct=approved_risk,
        max_risk_amount=risk_amount,
    )
