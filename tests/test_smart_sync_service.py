import pytest
from unittest.mock import AsyncMock, patch
from app.services.smart_sync_service import SmartSyncService
from app.models.webhook_signal import WebhookSignal
from app.models.config import AppConfig, SymbolConfig

@pytest.fixture
def smart_sync_service():
    return SmartSyncService()

@pytest.mark.asyncio
async def test_process_signal_symbol_not_in_config(smart_sync_service):
    # Mocking config service to return empty config and telegram service
    with (
        patch("app.services.smart_sync_service.config_service.get_config", new_callable=AsyncMock) as mock_get_config,
        patch("app.services.smart_sync_service.send_message", new_callable=AsyncMock) as mock_send_message
    ):
        mock_get_config.return_value = AppConfig(root={})
        
        signal = WebhookSignal(
            passphrase="pass",
            ticker="BTCUSDT",
            action="entry",
            side="long",
            qty=1.0
        )
        
        result = await smart_sync_service.process_signal(signal)
        assert result["status"] == "ignored"
        assert "not in config" in result["reason"]
        mock_send_message.assert_called_once()

@pytest.mark.asyncio
async def test_process_signal_symbol_paused(smart_sync_service):
    # Mocking config service to return paused config
    with patch("app.services.smart_sync_service.config_service.get_config", new_callable=AsyncMock) as mock_get_config:
        mock_get_config.return_value = AppConfig(root={
            "BTCUSDT": SymbolConfig(status="paused", multiplier=10.0)
        })
        
        signal = WebhookSignal(
            passphrase="pass",
            ticker="BTCUSDT",
            action="entry",
            side="long",
            qty=1.0
        )
        
        result = await smart_sync_service.process_signal(signal)
        assert result["status"] == "ignored"
        assert result["reason"] == "Paused"

@pytest.mark.asyncio
async def test_handle_entry_success(smart_sync_service):
    # Mocking config service and exchange service
    with (
        patch("app.services.smart_sync_service.config_service.get_config", new_callable=AsyncMock) as mock_get_config,
        patch("app.services.smart_sync_service.exchange_service.create_market_order", new_callable=AsyncMock) as mock_create_order,
        patch("app.services.smart_sync_service.send_message", new_callable=AsyncMock) as mock_send_message
    ):
        mock_get_config.return_value = AppConfig(root={
            "BTCUSDT": SymbolConfig(status="active", multiplier=10.0)
        })
        mock_create_order.return_value = {"retCode": 0, "result": {"id": "12345"}}
        
        signal = WebhookSignal(
            passphrase="pass",
            ticker="BTCUSDT",
            action="entry",
            side="long",
            qty=0.5
        )
        
        result = await smart_sync_service.process_signal(signal)
        assert result["status"] == "success"
        assert result["order_id"] == "12345"
        
        # Check if qty was multiplied (0.5 * 10.0 = 5.0)
        mock_create_order.assert_called_once_with(
            symbol="BTCUSDT",
            side="buy",
            amount=5.0
        )
        mock_send_message.assert_called_once()

@pytest.mark.asyncio
async def test_handle_close_all_success(smart_sync_service):
    # Mocking config service, exchange service.get_positions and create_market_order
    with (
        patch("app.services.smart_sync_service.config_service.get_config", new_callable=AsyncMock) as mock_get_config,
        patch("app.services.smart_sync_service.exchange_service.get_positions", new_callable=AsyncMock) as mock_get_positions,
        patch("app.services.smart_sync_service.exchange_service.create_market_order", new_callable=AsyncMock) as mock_create_order,
        patch("app.services.smart_sync_service.send_message", new_callable=AsyncMock) as mock_send_message
    ):
        mock_get_config.return_value = AppConfig(root={
            "BTCUSDT": SymbolConfig(status="active", multiplier=10.0)
        })
        mock_get_positions.return_value = {
            "retCode": 0,
            "result": {
                "list": [
                    {"side": "long", "contracts": "2.5"},
                    {"side": "short", "contracts": "0"}
                ]
            }
        }
        mock_create_order.return_value = {"retCode": 0, "result": {"id": "close_123"}}
        
        signal = WebhookSignal(
            passphrase="pass",
            ticker="BTCUSDT",
            action="close_all",
            side="long",
            qty=0.0
        )
        
        result = await smart_sync_service.process_signal(signal)
        assert result["status"] == "success"
        
        # Should close only the "long" position
        mock_create_order.assert_called_once_with(
            symbol="BTCUSDT",
            side="sell",
            amount=2.5,
            params={"reduceOnly": True}
        )
        mock_send_message.assert_called_once()
