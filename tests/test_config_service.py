import pytest
import os
import asyncio
from app.services.config_service import ConfigService
from app.models.config import AppConfig, SymbolConfig

@pytest.fixture
def test_config_path(tmp_path):
    return str(tmp_path / "config.json")

@pytest.fixture
def config_service(test_config_path):
    return ConfigService(config_path=test_config_path)

@pytest.mark.asyncio
async def test_get_config_empty(config_service):
    # If file doesn't exist, should return empty AppConfig
    config = await config_service.get_config()
    assert isinstance(config, AppConfig)
    assert config.root == {}

@pytest.mark.asyncio
async def test_save_and_get_config(config_service):
    new_config = AppConfig(root={
        "BTCUSDT": SymbolConfig(status="active", multiplier=10.0)
    })
    await config_service.save_config(new_config)
    
    saved_config = await config_service.get_config()
    assert saved_config.root["BTCUSDT"].status == "active"
    assert saved_config.root["BTCUSDT"].multiplier == 10.0

@pytest.mark.asyncio
async def test_update_symbol_config(config_service):
    # First save an initial config
    initial_config = AppConfig(root={
        "BTCUSDT": SymbolConfig(status="active", multiplier=1.0)
    })
    await config_service.save_config(initial_config)
    
    # Update one symbol
    new_symbol_config = SymbolConfig(status="paused", multiplier=5.0)
    await config_service.update_symbol_config("BTCUSDT", new_symbol_config)
    
    # Add another symbol
    eth_config = SymbolConfig(status="active", multiplier=2.0)
    await config_service.update_symbol_config("ETHUSDT", eth_config)
    
    final_config = await config_service.get_config()
    assert final_config.root["BTCUSDT"].status == "paused"
    assert final_config.root["BTCUSDT"].multiplier == 5.0
    assert final_config.root["ETHUSDT"].status == "active"
    assert final_config.root["ETHUSDT"].multiplier == 2.0

@pytest.mark.asyncio
async def test_concurrent_updates(config_service):
    # Simulate multiple concurrent updates to test the lock
    async def update_multiplier(symbol: str, mult: float):
        # We need to read-modify-write inside the lock which update_symbol_config does
        config = SymbolConfig(status="active", multiplier=mult)
        await config_service.update_symbol_config(symbol, config)

    # Run many updates concurrently
    tasks = [update_multiplier(f"SYM_{i}", float(i)) for i in range(10)]
    await asyncio.gather(*tasks)
    
    final_config = await config_service.get_config()
    assert len(final_config.root) == 10
    for i in range(10):
        assert final_config.root[f"SYM_{i}"].multiplier == float(i)

@pytest.mark.asyncio
async def test_read_corrupted_json(config_service, test_config_path):
    # Write invalid JSON to file
    with open(test_config_path, "w") as f:
        f.write("corrupted {")
        
    config = await config_service.get_config()
    assert config.root == {}
