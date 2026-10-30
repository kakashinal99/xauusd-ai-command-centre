"""FastAPI application entry point."""

from fastapi import FastAPI

from app.config import get_settings

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Backend foundation for a demo-first XAUUSD trading research platform.",
)


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {"name": settings.app_name, "status": "online", "environment": settings.app_env}


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(f"{settings.api_v1_prefix}/status", tags=["system"])
def api_status() -> dict[str, str]:
    return {
        "status": "ok",
        "environment": settings.app_env,
        "trading_mode": "disabled",
        "broker": "ctrader",
        "market": "XAUUSD",
    }
