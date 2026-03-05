from fastapi import APIRouter, HTTPException, Depends
from app.services.trade_service import trade_service
from app.services.config_service import config_service
from app.models.config import GlobalSettings

from app.core.security import verify_telegram_webapp_data

router = APIRouter(prefix="/api/status", tags=["status"], dependencies=[Depends(verify_telegram_webapp_data)])

@router.get("/balance")
async def get_balance():
    """
    Returns the account balance from the exchange.
    """
    try:
        from app.services.exchange_service import exchange_service
        balance_data = await exchange_service.get_balance()
        if balance_data.get("retCode") == 0:
            # We want to return a simplified version for the WebApp
            # Usually USDT balance is what matters for perpetuals
            res = balance_data.get("result", {})
            return {
                "total": res.get("total", {}).get("USDT", 0),
                "free": res.get("free", {}).get("USDT", 0),
                "used": res.get("used", {}).get("USDT", 0)
            }
        return {"total": 0, "free": 0, "used": 0, "error": balance_data.get("retMsg")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active_positions")
async def get_active_positions():
    """
    Returns all active positions from the database for the WebApp.
    """
    try:
        # We'll need a new method in trade_service to get ALL active positions
        positions = await trade_service.get_all_active_positions()
        return [
            {
                "symbol": p.symbol,
                "side": p.side,
                "quantity": p.total_quantity,
                "avg_price": p.average_entry_price,
                "entry_time": p.entry_time.isoformat() if p.entry_time else None,
                "fills_count": len(p.fills)
            } for p in positions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/global_settings")
async def get_global_settings():
    config = await config_service.get_config()
    return config.settings

@router.post("/global_settings")
async def update_global_settings(settings: GlobalSettings):
    await config_service.update_global_settings(settings)
    return {"status": "success"}
