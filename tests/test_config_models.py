import pytest
from pydantic import ValidationError
from app.models.config import SymbolConfig, AppConfig

def test_symbol_config_valid():
    data = {"status": "active", "multiplier": 10.0}
    config = SymbolConfig(**data)
    assert config.status == "active"
    assert config.multiplier == 10.0

def test_symbol_config_invalid_status():
    data = {"status": "not_existing", "multiplier": 10.0}
    with pytest.raises(ValidationError):
        SymbolConfig(**data)

def test_symbol_config_negative_multiplier():
    data = {"status": "active", "multiplier": -1.0}
    with pytest.raises(ValidationError):
        SymbolConfig(**data)

def test_app_config_valid():
    data = {
        "BTCUSDT": {"status": "active", "multiplier": 10.0},
        "ETHUSDT": {"status": "paused_for_entries", "multiplier": 5.0}
    }
    config = AppConfig(data)
    assert "BTCUSDT" in config.root
    assert config.root["BTCUSDT"].multiplier == 10.0
    assert config.root["ETHUSDT"].status == "paused_for_entries"

def test_app_config_invalid():
    data = {
        "BTCUSDT": {"status": "active", "multiplier": "not_a_float"}
    }
    with pytest.raises(ValidationError):
        AppConfig(data)
