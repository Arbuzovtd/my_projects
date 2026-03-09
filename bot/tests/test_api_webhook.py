import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from main import app
from app.core.settings import settings

client = TestClient(app)

def test_webhook_success():
    payload = {
        "passphrase": settings.WEBHOOK_PASSPHRASE,
        "ticker": "BTCUSDT",
        "action": "entry",
        "side": "long",
        "qty": 1.0
    }
    with patch("app.api.webhook.smart_sync_service.process_signal", new_callable=AsyncMock) as mock_process:
        mock_process.return_value = {"status": "success", "order_id": "test_id"}
        response = client.post("/webhook", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "success"

def test_webhook_invalid_passphrase():
    payload = {
        "passphrase": "wrong_passphrase",
        "ticker": "BTCUSDT",
        "action": "entry",
        "side": "long",
        "qty": 1.0
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid passphrase"

def test_webhook_invalid_payload():
    payload = {
        "passphrase": settings.WEBHOOK_PASSPHRASE,
        "ticker": "BTCUSDT"
        # Missing action, side, qty
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 422
