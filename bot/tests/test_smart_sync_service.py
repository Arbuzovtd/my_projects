import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.smart_sync_service import SmartSyncService
from app.models.webhook_signal import WebhookSignal
from app.models.config import AppConfig, SymbolConfig

@pytest.fixture
def smart_sync_service():
    return SmartSyncService()

@pytest.mark.asyncio
async def test_process_signal_symbol_not_in_config(smart_sync_service):
    with (
        patch("app.services.smart_sync_service.config_service.get_config", new_callable=AsyncMock) as mock_get_config,
        patch("app.services.smart_sync_service.send_message", new_callable=AsyncMock) as mock_send_message
    ):
        mock_get_config.return_value = AppConfig(symbols={})
        
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

@pytest.mark.asyncio
async def test_handle_entry_success(smart_sync_service):
    with (
        patch("app.services.smart_sync_service.config_service.get_config", new_callable=AsyncMock) as mock_get_config,
        patch("app.services.smart_sync_service.exchange_service.create_market_order", new_callable=AsyncMock) as mock_create_order,
        patch("app.services.smart_sync_service.exchange_service.set_leverage", new_callable=AsyncMock),
        patch("app.services.smart_sync_service.trade_service.record_entry", new_callable=AsyncMock),
        patch("app.services.smart_sync_service.send_message", new_callable=AsyncMock)
    ):
        mock_get_config.return_value = AppConfig(symbols={
            "BTCUSDT": SymbolConfig(status="active", multiplier=10.0, leverage=10)
        })

        mock_create_order.return_value = {"retCode": 0, "result": {"id": "12345", "price": 50000}}
        
        signal = WebhookSignal(
            passphrase="pass",
            ticker="BTCUSDT",
            action="entry",
            side="long",
            qty=0.5
        )
        
        result = await smart_sync_service.process_signal(signal)
        assert result["status"] == "success"
        
        mock_create_order.assert_called_once_with(
            symbol="BTCUSDT",
            side="buy",
            amount=5.0,
            params={"recvWindow": 60000}
        )

@pytest.mark.asyncio
async def test_handle_close_all_full(smart_sync_service):
    with (
        patch("app.services.smart_sync_service.config_service.get_config", new_callable=AsyncMock) as mock_get_config,
        patch("app.services.smart_sync_service.trade_service.get_active_position", new_callable=AsyncMock) as mock_get_pos,
        patch("app.services.smart_sync_service.trade_service.record_close", new_callable=AsyncMock) as mock_record_close,
        patch("app.services.smart_sync_service.exchange_service.create_market_order", new_callable=AsyncMock) as mock_create_order,
        patch("app.services.smart_sync_service.send_message", new_callable=AsyncMock)
    ):
        mock_get_config.return_value = AppConfig(symbols={
            "BTCUSDT": SymbolConfig(status="active", multiplier=10.0)
        })

        # DB has 5.0 units
        mock_pos = MagicMock()
        mock_pos.side = "long"
        mock_pos.total_quantity = 5.0
        mock_pos.average_entry_price = 40000
        mock_get_pos.return_value = mock_pos
        
        mock_create_order.return_value = {"retCode": 0, "result": {"id": "close_123", "average": 41000}}
        
        # Signal with qty=0 (full close)
        signal = WebhookSignal(
            passphrase="pass",
            ticker="BTCUSDT",
            action="close_all",
            side="long",
            qty=0.0
        )
        
        result = await smart_sync_service.process_signal(signal)
        assert result["status"] == "success"
        
        # Should close ALL 5.0
        mock_create_order.assert_called_once_with(
            symbol="BTCUSDT",
            side="sell",
            amount=5.0,
            params={"reduceOnly": True, "recvWindow": 60000}
        )
        mock_record_close.assert_called_once_with(
            symbol="BTCUSDT",
            exit_price=41000,
            exit_reason="exit_signal",
            quantity=5.0
        )

@pytest.mark.asyncio
async def test_handle_close_all_partial(smart_sync_service):
    with (
        patch("app.services.smart_sync_service.config_service.get_config", new_callable=AsyncMock) as mock_get_config,
        patch("app.services.smart_sync_service.trade_service.get_active_position", new_callable=AsyncMock) as mock_get_pos,
        patch("app.services.smart_sync_service.trade_service.record_close", new_callable=AsyncMock) as mock_record_close,
        patch("app.services.smart_sync_service.exchange_service.create_market_order", new_callable=AsyncMock) as mock_create_order,
        patch("app.services.smart_sync_service.send_message", new_callable=AsyncMock)
    ):
        mock_get_config.return_value = AppConfig(symbols={
            "BTCUSDT": SymbolConfig(status="active", multiplier=10.0)
        })

        # DB has 5.0 units
        mock_pos = MagicMock()
        mock_pos.side = "long"
        mock_pos.total_quantity = 5.0
        mock_pos.average_entry_price = 40000
        mock_get_pos.return_value = mock_pos
        
        mock_create_order.return_value = {"retCode": 0, "result": {"id": "close_partial", "average": 41000}}
        
        # Signal with qty=0.2 (partial close: 0.2 * 10 = 2.0 units)
        signal = WebhookSignal(
            passphrase="pass",
            ticker="BTCUSDT",
            action="close_all",
            side="long",
            qty=0.2
        )
        
        result = await smart_sync_service.process_signal(signal)
        assert result["status"] == "success"
        
        # Should close only 2.0
        mock_create_order.assert_called_once_with(
            symbol="BTCUSDT",
            side="sell",
            amount=2.0,
            params={"reduceOnly": True, "recvWindow": 60000}
        )
        mock_record_close.assert_called_once_with(
            symbol="BTCUSDT",
            exit_price=41000,
            exit_reason="exit_signal",
            quantity=2.0
        )
