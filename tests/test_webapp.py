import pytest
from fastapi.testclient import TestClient
from main import app
import os
import json
from app.core.settings import settings

client = TestClient(app)

@pytest.fixture
def temp_config_file(tmp_path):
    """
    Creates a temporary config file for testing.
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "config.json"
    
    initial_config = {
        "BTCUSDT": {
            "status": "active",
            "multiplier": 1.0
        }
    }
    
    with open(config_file, "w") as f:
        json.dump(initial_config, f)
    
    original_path = settings.CONFIG_PATH
    settings.CONFIG_PATH = str(config_file)
    
    yield config_file
    
    settings.CONFIG_PATH = original_path

def test_static_index_exists():
    """
    Verifies that the static index.html is accessible.
    """
    response = client.get("/static/index.html")
    assert response.status_code == 200
    assert "Multiplier Manager" in response.text
    assert "telegram-web-app.js" in response.text

def test_get_config_api(temp_config_file):
    """
    Tests the GET /api/config endpoint.
    """
    response = client.get("/api/config/")
    assert response.status_code == 200
    data = response.json()
    assert "BTCUSDT" in data
    assert data["BTCUSDT"]["multiplier"] == 1.0
    assert data["BTCUSDT"]["status"] == "active"

def test_update_symbol_config_api(temp_config_file):
    """
    Tests the POST /api/config/{symbol} endpoint.
    """
    update_data = {
        "status": "paused",
        "multiplier": 2.5
    }
    response = client.post("/api/config/BTCUSDT", json=update_data)
    assert response.status_code == 200
    assert response.json() == update_data
    
    # Verify it was saved to the file
    with open(temp_config_file, "r") as f:
        saved_config = json.load(f)
        assert saved_config["BTCUSDT"]["status"] == "paused"
        assert saved_config["BTCUSDT"]["multiplier"] == 2.5

def test_update_invalid_config_api(temp_config_file):
    """
    Tests the POST /api/config/{symbol} endpoint with invalid data.
    """
    invalid_data = {
        "status": "invalid_status",
        "multiplier": -1.0
    }
    response = client.post("/api/config/BTCUSDT", json=invalid_data)
    assert response.status_code == 422  # Validation error
