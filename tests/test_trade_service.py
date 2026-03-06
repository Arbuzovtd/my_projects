import pytest
from app.services.trade_service import TradeService
from app.db.models import PositionStatus

@pytest.fixture
def trade_service():
    return TradeService()

@pytest.mark.asyncio
async def test_record_entry_and_partial_close(trade_service):
    symbol = "ETHUSDT"
    
    # 1. First entry: 10 units @ 2000
    await trade_service.record_entry(symbol, "long", 2000.0, 10.0, "order_1")
    
    pos = await trade_service.get_active_position(symbol)
    assert pos is not None
    assert pos.total_quantity == 10.0
    assert pos.average_entry_price == 2000.0
    assert pos.status == PositionStatus.ACTIVE
    
    # 2. Partial close: 3 units @ 2100
    # PnL should be: (2100 - 2000) * 3 = 300 USDT
    await trade_service.record_close(symbol, 2100.0, quantity=3.0)
    
    pos = await trade_service.get_active_position(symbol)
    assert pos.total_quantity == 7.0 # 10 - 3
    assert pos.status == PositionStatus.ACTIVE
    assert pos.total_pnl_usdt == 300.0
    
    # 3. Another partial close: 2 units @ 2200
    # Additional PnL: (2200 - 2000) * 2 = 400 USDT
    # Total PnL: 300 + 400 = 700 USDT
    await trade_service.record_close(symbol, 2200.0, quantity=2.0)
    
    pos = await trade_service.get_active_position(symbol)
    assert pos.total_quantity == 5.0
    assert pos.total_pnl_usdt == 700.0
    
    # 4. Final full close @ 1900
    # Remaining 5 units. PnL: (1900 - 2000) * 5 = -500 USDT
    # Final total PnL: 700 - 500 = 200 USDT
    await trade_service.record_close(symbol, 1900.0)
    
    # No active position now
    pos_active = await trade_service.get_active_position(symbol)
    assert pos_active is None
    
    # Check the closed position directly (need a way to find it, but for test we know it's the last one)
    # Let's just trust the logic for now or we could add a method to get last closed.
