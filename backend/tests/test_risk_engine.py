from decimal import Decimal

from app.risk.engine import evaluate_risk
from app.risk.schemas import RiskCheckRequest, RiskLimits


def valid_request(**overrides) -> RiskCheckRequest:
    values = {
        "equity": Decimal("10000"),
        "day_start_equity": Decimal("10000"),
        "week_start_equity": Decimal("10000"),
        "peak_equity": Decimal("10000"),
        "requested_risk_pct": Decimal("0.25"),
        "open_positions": 0,
        "has_stop_loss": True,
        "kill_switch_active": False,
        "trading_enabled": True,
    }
    values.update(overrides)
    return RiskCheckRequest(**values)


def test_allows_trade_within_limits_and_calculates_risk_amount() -> None:
    result = evaluate_risk(valid_request())
    assert result.allowed is True
    assert result.approved_risk_pct == Decimal("0.25")
    assert result.max_risk_amount == Decimal("25.00")
    assert result.reasons == []


def test_trading_disabled_fails_closed_by_default() -> None:
    result = evaluate_risk(valid_request(trading_enabled=False))
    assert result.allowed is False
    assert result.approved_risk_pct == 0
    assert "Trading is disabled" in result.reasons


def test_kill_switch_blocks_trade() -> None:
    result = evaluate_risk(valid_request(kill_switch_active=True))
    assert result.allowed is False
    assert "Kill switch is active" in result.reasons


def test_requires_stop_loss() -> None:
    result = evaluate_risk(valid_request(has_stop_loss=False))
    assert result.allowed is False
    assert "A stop loss is required" in result.reasons


def test_daily_loss_limit_blocks_trade() -> None:
    result = evaluate_risk(valid_request(equity=Decimal("9800")))
    assert result.allowed is False
    assert "Daily loss limit reached" in result.reasons


def test_weekly_loss_limit_blocks_trade() -> None:
    result = evaluate_risk(valid_request(
        equity=Decimal("9600"), day_start_equity=Decimal("10000"),
        week_start_equity=Decimal("10000"),
    ))
    assert result.allowed is False
    assert "Weekly loss limit reached" in result.reasons


def test_drawdown_limit_blocks_trade() -> None:
    result = evaluate_risk(valid_request(equity=Decimal("9400")))
    assert result.allowed is False
    assert "Maximum drawdown limit reached" in result.reasons


def test_open_position_limit_blocks_second_position() -> None:
    result = evaluate_risk(valid_request(open_positions=1))
    assert result.allowed is False
    assert "Maximum open positions reached" in result.reasons


def test_per_trade_limit_is_enforced() -> None:
    result = evaluate_risk(valid_request(requested_risk_pct=Decimal("0.5")))
    assert result.allowed is False
    assert "Requested risk exceeds the per-trade limit" in result.reasons


def test_limits_can_be_configured_but_not_overridden_by_request() -> None:
    limits = RiskLimits(max_risk_per_trade_pct=Decimal("0.10"))
    result = evaluate_risk(valid_request(), limits)
    assert result.allowed is False
    assert result.approved_risk_pct == 0
