import pytest
from fastapi.testclient import TestClient
from main import app
from app.services.config_service import config_service
import os
import json

client = TestClient(app)

@pytest.fixture
def temp_config_file(tmp_path):
    """
    Creates a temporary configuration file for testing.
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "config.json"
    
    initial_config = {
        "settings": {"exchange_id": "okx", "use_testnet": True},
        "symbols": {
            "BTCUSDT": {"status": "active", "multiplier": 1.0, "leverage": 1}
        }
    }
    
    with open(config_file, "w") as f:
        json.dump(initial_config, f)
    
    # Override the config_path in config_service
    original_path = config_service._config_path
    config_service._config_path = str(config_file)
    
    yield config_file
    
    # Restore the original path
    config_service._config_path = original_path

def test_static_index_exists():
    """
    Verifies that the static index.html is accessible.
    """
    response = client.get("/static/index.html")
    assert response.status_code == 200
    assert "Trade Bot Settings" in response.text

def test_get_config_api(temp_config_file):
    """
    Tests the GET /api/config endpoint.
    """
    response = client.get("/api/config/")
    assert response.status_code == 200
    data = response.json()
    assert "symbols" in data
    assert "BTCUSDT" in data["symbols"]

def test_update_symbol_config_api(temp_config_file):
    """
    Tests the POST /api/config/symbols/{symbol} endpoint.
    """
    update_data = {
        "status": "paused",
        "multiplier": 2.5,
        "leverage": 5
    }
    response = client.post("/api/config/symbols/BTCUSDT", json=update_data)
    assert response.status_code == 200
    
    # Verify the update
    get_response = client.get("/api/config/symbols")
    assert get_response.json()["BTCUSDT"]["status"] == "paused"
    assert get_response.json()["BTCUSDT"]["multiplier"] == 2.5
    assert get_response.json()["BTCUSDT"]["leverage"] == 5

def test_update_invalid_config_api(temp_config_file):
    """
    Tests the POST /api/config/symbols/{symbol} endpoint with invalid data.
    """
    invalid_data = {
        "status": "invalid_status",
        "multiplier": -1.0
    }
    response = client.post("/api/config/symbols/BTCUSDT", json=invalid_data)
    assert response.status_code == 422  # Validation error
