from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_trading_is_disabled_in_initial_scaffold() -> None:
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    assert response.json()["trading_mode"] == "disabled"
    assert response.json()["market"] == "XAUUSD"
