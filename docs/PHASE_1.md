# Phase 1 — Project foundation

## Scope
- Establish a Python/FastAPI backend.
- Add environment-based configuration without committing credentials.
- Provide health and status endpoints for deployment checks.
- Prepare a Docker image for cloud hosting.

## Safety defaults
- Broker environment defaults to cTrader demo.
- Trading mode is explicitly disabled.
- No order placement, strategy activation, or live-account connection is implemented in this phase.
- API secrets and OAuth tokens must stay in environment variables or a secrets manager, never in Git.

## Local run

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cd backend
uvicorn app.main:app --reload
```

Check:
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/api/v1/status`
- `http://127.0.0.1:8000/docs`

## Next
After the cTrader Open API application is approved, implement OAuth authorization and a read-only demo connection for XAUUSD market data. Do not enable execution until the risk controls and validation gates are implemented and tested.
