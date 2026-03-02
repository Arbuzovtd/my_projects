import pytest
from pydantic import ValidationError
from app.models.config import SymbolConfig, AppConfig, GlobalSettings

def test_symbol_config_valid():
    data = {"status": "active", "multiplier": 10.0, "leverage": 5}
    config = SymbolConfig(**data)
    assert config.status == "active"
    assert config.multiplier == 10.0
    assert config.leverage == 5

def test_symbol_config_invalid():
    # Multiplier must be >= 0
    with pytest.raises(ValidationError):
        SymbolConfig(status="active", multiplier=-1.0)
    
    # Leverage must be >= 1
    with pytest.raises(ValidationError):
        SymbolConfig(status="active", multiplier=1.0, leverage=0)
    
    # Status must be one of the allowed literals
    with pytest.raises(ValidationError):
        SymbolConfig(status="invalid_status", multiplier=1.0)

def test_app_config_valid():
    data = {
        "symbols": {
            "BTCUSDT": {"status": "active", "multiplier": 10.0},
            "ETHUSDT": {"status": "paused_for_entries", "multiplier": 5.0}
        },
        "settings": {"exchange_id": "bybit", "use_testnet": False}
    }
    config = AppConfig(**data)
    assert "BTCUSDT" in config.symbols
    assert config.symbols["BTCUSDT"].status == "active"
    assert config.settings.exchange_id == "bybit"
    assert config.settings.use_testnet is False

def test_app_config_invalid():
    data = {
        "symbols": {
            "BTCUSDT": {"status": "active", "multiplier": "not_a_float"}
        }
    }
    with pytest.raises(ValidationError):
        AppConfig(**data)
