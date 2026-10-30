# Independent risk engine

## Purpose
The risk engine is deterministic Python code. It is separate from AI agents and is the final policy check before any future order-execution service. It does not place, modify or close orders.

## Initial configurable limits
These are starting values for demo development, not a promise of profitability or a final live-risk recommendation:

| Control | Initial value |
|---|---:|
| Maximum risk per trade | 0.25% of current equity |
| Maximum daily loss | 2.0% from day-start equity |
| Maximum weekly loss | 4.0% from week-start equity |
| Maximum peak-to-current drawdown | 6.0% |
| Concurrent open positions | 1 |

Limits are configurable in code at this stage. Later they will be stored in protected deployment configuration with an audited change process.

## Blocking conditions
A proposal is rejected if trading is disabled, kill switch is active, no stop loss is present, requested risk exceeds the per-trade limit, the position cap is reached, or any daily/weekly/drawdown limit is reached.

The engine fails closed: rejected proposals receive zero approved risk. It uses account equity (not balance) so floating P&L is included when the caller supplies a current equity snapshot.

## Important limitations
- The engine currently evaluates a supplied account snapshot; it does not yet retrieve equity or positions from cTrader.
- It does not calculate lots/units. That requires verified Pepperstone XAUUSD contract specifications, volume step, minimum size, and stop-distance rules.
- Daily/weekly reset boundaries and peak-equity persistence must be implemented and tested against broker/account timezone before any live use.
- The kill switch is currently an input flag, not yet a persistent operator control.
- No endpoint in this phase can enable trading or execute an order.

## Validation
Unit tests cover normal approval, default-disabled behavior, kill switch, missing stop loss, per-trade cap, position cap and daily/weekly/drawdown stops.
