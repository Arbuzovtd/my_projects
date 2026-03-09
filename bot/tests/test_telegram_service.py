import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram import types
from app.services.telegram_service import cmd_start, cmd_status, send_message
from app.models.config import AppConfig, SymbolConfig, GlobalSettings

@pytest.mark.asyncio
async def test_cmd_start(monkeypatch):
    # Mock settings
    monkeypatch.setattr("app.services.telegram_service.settings.WEBAPP_URL", "http://test.com")
    monkeypatch.setattr("app.services.telegram_service.settings.EXCHANGE_ID", "bybit")

    # Setup mock message
    message = AsyncMock(spec=types.Message)
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
    assert "👋 Привет! Я торговый робот." in args[0]
    assert "http://test.com/static/index.html" in str(kwargs["reply_markup"])

@pytest.mark.asyncio
async def test_cmd_status_empty(monkeypatch):
    # Setup empty config
    empty_config = AppConfig(symbols={})
    
    # Mock config_service
    mock_get_config = AsyncMock(return_value=empty_config)
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
    sample_config = AppConfig(
        settings=GlobalSettings(exchange_id="bybit", use_testnet=True),
        symbols={
            "BTCUSDT": SymbolConfig(status="active", multiplier=1.1, leverage=5),
            "ETHUSDT": SymbolConfig(status="paused", multiplier=2.2, leverage=1)
        }
    )

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
    # Check for presence of key data rather than exact formatting
    assert "Текущий статус робота" in response_text
    assert "BYBIT" in response_text
    assert "TESTNET" in response_text
    assert "BTCUSDT" in response_text
    assert "1.1" in response_text
    assert "2.2" in response_text
    assert "5" in response_text

@pytest.mark.asyncio
async def test_send_message_success(monkeypatch):
    # Mock bot.send_message
    mock_send = AsyncMock()
    monkeypatch.setattr("app.services.telegram_service.bot.send_message", mock_send)
    monkeypatch.setattr("app.services.telegram_service.settings.TELEGRAM_CHAT_ID", "123456")

    result = await send_message("Test message")
    
    assert result is True
    mock_send.assert_called_once_with("123456", "Test message", parse_mode="HTML")

@pytest.mark.asyncio
async def test_send_message_no_chat_id(monkeypatch):
    monkeypatch.setattr("app.services.telegram_service.settings.TELEGRAM_CHAT_ID", "")
    
    result = await send_message("Test message")
    assert result is False
