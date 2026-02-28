import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Patch aiogram.Bot before importing the service to avoid TokenValidationError
with patch("aiogram.Bot"):
    from app.services.telegram_service import cmd_start, cmd_status
from aiogram import types
from app.models.config import AppConfig, SymbolConfig

@pytest.mark.asyncio
async def test_cmd_start():
    # Setup mock message
    message = AsyncMock()
    message.from_user = MagicMock()
    message.from_user.id = 123
    message.chat = MagicMock()
    message.chat.id = 456
    message.answer = AsyncMock()
    
    # Run the handler
    await cmd_start(message)
    
    # Assert
    message.answer.assert_called_once()
    args, kwargs = message.answer.call_args
    assert "👋 Привет!" in args[0]
    assert "Chat ID" in args[0]
    assert "456" in args[0]

@pytest.mark.asyncio
async def test_cmd_status_empty(monkeypatch):
    # Mock config_service
    mock_get_config = AsyncMock(return_value=AppConfig(root={}))
    monkeypatch.setattr("app.services.telegram_service.config_service.get_config", mock_get_config)
    
    # Setup mock message
    message = AsyncMock(spec=types.Message)
    message.answer = AsyncMock()
    
    # Run the handler
    await cmd_status(message)
    
    # Assert
    message.answer.assert_called_once_with("⚠️ Конфигурация пуста или не загружена.")

@pytest.mark.asyncio
async def test_cmd_status_with_data(monkeypatch):
    # Setup sample config
    sample_config = AppConfig(root={
        "BTCUSDT": SymbolConfig(status="active", multiplier=10.0),
        "ETHUSDT": SymbolConfig(status="paused", multiplier=5.0)
    })
    
    # Mock config_service
    mock_get_config = AsyncMock(return_value=sample_config)
    monkeypatch.setattr("app.services.telegram_service.config_service.get_config", mock_get_config)
    
    # Setup mock message
    message = AsyncMock(spec=types.Message)
    message.answer = AsyncMock()
    
    # Run the handler
    await cmd_status(message)
    
    # Assert
    message.answer.assert_called_once()
    args, kwargs = message.answer.call_args
    response_text = args[0]
    assert "📈 Текущий статус робота:" in response_text
    assert "BTCUSDT" in response_text
    assert "active" in response_text
    assert "multiplier" in response_text.lower() or "мультипликатор" in response_text.lower()
    assert "ETHUSDT" in response_text
    assert "paused" in response_text
