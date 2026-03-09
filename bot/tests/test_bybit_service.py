import pytest
from unittest.mock import MagicMock, patch
from app.services.bybit_service import BybitClient

@pytest.fixture
def mock_bybit_session():
    with patch("app.services.bybit_service.HTTP") as mock_http:
        mock_instance = MagicMock()
        mock_http.return_value = mock_instance
        yield mock_instance

@pytest.mark.asyncio
async def test_bybit_client_init(mock_bybit_session):
    client = BybitClient(api_key="test_key", api_secret="test_secret", testnet=True)
    assert client.api_key == "test_key"
    assert client.api_secret == "test_secret"
    assert client.testnet is True

@pytest.mark.asyncio
async def test_get_wallet_balance_success(mock_bybit_session):
    mock_bybit_session.get_wallet_balance.return_value = {"retCode": 0, "retMsg": "OK", "result": {"list": []}}
    
    client = BybitClient(api_key="key", api_secret="secret")
    result = await client.get_wallet_balance(account_type="UNIFIED")
    
    assert result["retCode"] == 0
    assert result["retMsg"] == "OK"
    mock_bybit_session.get_wallet_balance.assert_called_once_with(accountType="UNIFIED", coin=None)

@pytest.mark.asyncio
async def test_get_wallet_balance_failure(mock_bybit_session):
    mock_bybit_session.get_wallet_balance.side_effect = Exception("API Error")
    
    client = BybitClient(api_key="key", api_secret="secret")
    result = await client.get_wallet_balance(account_type="UNIFIED")
    
    assert result["retCode"] == -1
    assert "API Error" in result["retMsg"]

@pytest.mark.asyncio
async def test_place_order_success(mock_bybit_session):
    mock_bybit_session.place_order.return_value = {"retCode": 0, "retMsg": "OK", "result": {"orderId": "123"}}
    
    client = BybitClient(api_key="key", api_secret="secret")
    result = await client.place_order(
        category="linear",
        symbol="BTCUSDT",
        side="Buy",
        order_type="Market",
        qty="0.001"
    )
    
    assert result["retCode"] == 0
    assert result["result"]["orderId"] == "123"
    mock_bybit_session.place_order.assert_called_once_with(
        category="linear",
        symbol="BTCUSDT",
        side="Buy",
        orderType="Market",
        qty="0.001"
    )
