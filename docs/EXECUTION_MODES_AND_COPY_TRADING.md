# Execution Modes and Copy-Trading Architecture

**Status:** Approved product requirement  
**Product:** XAUUSD AI Command Centre  
**Decision:** Optional execution — every end user can choose manual signals or broker-connected auto-copy.

## 1. Product model

The platform is a centralised signal and trading-intelligence service:

- The administrator operates the central market analysis, research, strategy, risk and signal-publishing functions.
- End users consume centrally published signals and verified performance.
- End users may optionally connect their own supported broker account and enable automatic execution.
- Each user's trades are placed in that user's own broker account, using that user's funds and execution preferences.
- Connecting a broker must never automatically enable trading. Auto-copy requires a separate, explicit opt-in.

## 2. User execution modes

Each user can select either mode and change it later:

### Manual signal mode
- Receive published BUY/SELL signals and notifications.
- View entry reference, stop loss, take profit, signal status, timestamps and performance.
- Place and manage orders independently with their own broker.
- No broker trading permission is required for this mode.

### Auto-copy mode
- User connects an individually owned broker account through the broker's supported authorisation flow.
- User explicitly enables auto-copy after reviewing and accepting the execution and risk settings.
- The execution service translates each eligible central signal into an order for that user's account.
- Each account uses its own risk/lot settings, symbol mapping and execution constraints.
- User can pause or disable auto-copy and disconnect the broker at any time.
- A connected account remains in manual mode until auto-copy is explicitly enabled.

## 3. Roles and permissions

### Administrator
- Full access to market monitoring, research, strategy testing, strategy activation, risk controls and signal publishing.
- Can publish, pause, cancel or close centrally managed signals according to the signal lifecycle policy.
- Can monitor aggregate execution health and anonymised/authorised execution outcomes.
- Cannot view or disclose a user's broker password or raw credentials.
- Must not silently change an individual user's execution risk settings.

### End user
- Can view signals and published performance.
- Can manage their own broker connection, execution mode and risk preferences.
- Can view only their own broker connection metadata, orders, positions and execution history.
- Cannot access administrator research tools, strategy settings or another user's private data.

## 4. High-level architecture

1. Shared XAUUSD market-data ingestion.
2. Central AI / strategy / signal engine.
3. Signal validation and administrator publishing controls.
4. Central signal store and event distribution.
5. User preference and entitlement service.
6. Execution manager with broker-specific adapters.
7. Per-user broker connections and execution state.
8. Per-user execution history and performance views.
9. Notifications and user dashboard.

The signal is generated once centrally. Distribution and execution are performed per eligible user. A user in manual mode receives the signal but no order is sent to a broker.

## 5. Broker integration strategy

- **Initial target:** cTrader Open API, subject to application approval, OAuth implementation and broker/account compatibility.
- **Next target:** MetaTrader 5 through a separately designed and tested integration/bridge.
- Other brokers/platforms are supported only where a documented, authorised execution API or approved bridge exists.
- Broker adapters must normalise symbol names, volume units, order types, price precision, minimum/maximum volume, stop-distance rules and supported order operations.
- Broker integration must use each broker's supported authorisation mechanism. Never ask users to submit their broker trading password to the platform.

## 6. Per-user execution settings

Each connected account must have its own settings, including:

- Execution mode: manual or auto-copy.
- Account/environment: demo or live.
- Fixed lot or risk-based sizing (where reliably supported).
- Maximum risk per trade and maximum total exposure.
- Maximum simultaneous positions.
- Allowed symbol(s), initially XAUUSD.
- Maximum spread/slippage tolerance.
- Optional trading-session restrictions.
- Emergency pause / kill switch.

Defaults must be safe: manual mode, auto-copy disabled, and no live order execution until the user explicitly opts in and all required checks pass.

## 7. Execution safety and reliability requirements

- Enforce risk checks immediately before every broker order.
- Use idempotency keys based on signal, user account and execution attempt to prevent duplicate orders.
- Persist order intent and execution state before/after external broker calls.
- Handle rejected, delayed, partially filled, cancelled and unknown-status orders.
- Reconcile platform state against broker positions and orders.
- Do not blindly retry an order when the broker response is ambiguous; reconcile first.
- Respect each user's independent settings and never assume the administrator's lot size applies to subscribers.
- Validate spread, slippage, price freshness, symbol availability, market hours and broker constraints.
- Define consistent policies for signal updates, SL/TP changes, cancellation and closing positions.
- If market data, risk checks, database state or broker connectivity is unavailable or stale, fail closed: do not open new trades.
- Provide user-level pause/disconnect controls and an administrator-wide emergency execution stop.
- Keep an immutable audit trail of published signals, user consent/settings changes, order intents, broker responses and execution outcomes.
- Encrypt broker access and refresh tokens at rest; restrict access and never expose tokens to frontend clients or logs.

## 8. Signal and performance integrity

- Every published signal receives a stable unique ID and immutable publication timestamp.
- Signal status transitions must be recorded (for example: published, active, target hit, stop hit, cancelled, expired).
- Historical signals and outcomes must not be silently rewritten.
- Central signal performance must be distinguished from each user's actual broker execution performance.
- User execution results must account for that user's actual fills, spread, commission, swap, slippage and account currency where available.
- Clearly label indicative signal prices versus actual broker fills.

## 9. Delivery phases

1. Central signal publication and manual signal consumption.
2. User accounts, subscription entitlements and signal notifications.
3. cTrader demo account authorisation and connection health.
4. cTrader demo auto-copy with risk limits, idempotency and reconciliation.
5. Failure/recovery, load, security and execution-integrity testing.
6. Compliance review and broker/platform approval checks before any live auto-copy release.
7. Live auto-copy only after explicit user consent, operational sign-off and all required legal/regulatory checks.
8. MT5 integration as a separate adapter and release phase.

## 10. Explicit non-goals for the initial release

- No user-operated AI research or backtesting engine.
- No automatic live trading by default.
- No collection or storage of broker passwords.
- No guarantee that subscriber fills or performance match the central signal.
- No live execution before demo validation, security review, risk controls and compliance clearance.

## 11. Release acceptance criteria

- A user can use manual mode without connecting a broker.
- A connected broker account remains non-trading until auto-copy is explicitly enabled.
- A user can pause auto-copy and disconnect their broker.
- One published signal creates at most one intended execution per eligible user/account, with safe reconciliation for ambiguous broker responses.
- Risk limits are independently enforced per user account.
- One user's broker credentials, orders, positions and execution history are inaccessible to other users.
- Backend, database, market-data or broker failures prevent unsafe new orders and are clearly surfaced in the UI.
- Signal history and central performance remain auditable and separate from actual per-user execution performance.
