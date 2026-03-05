from fastapi import APIRouter, HTTPException, Depends
from typing import Dict
from app.models.config import AppConfig, SymbolConfig, GlobalSettings
from app.services.config_service import config_service

from app.core.security import verify_telegram_webapp_data

router = APIRouter(prefix="/api/config", tags=["config"], dependencies=[Depends(verify_telegram_webapp_data)])

@router.get("", response_model=AppConfig)
async def get_full_config():
    """
    Returns the full application configuration.
    """
    return await config_service.get_config()

@router.get("/symbols", response_model=Dict[str, SymbolConfig])
async def get_symbols_config():
    """
    Returns the current application configuration for symbols.
    """
    config = await config_service.get_config()
    return config.symbols

@router.post("/settings", response_model=GlobalSettings)
async def update_global_settings(global_settings: GlobalSettings):
    """
    Updates the global settings (exchange, testnet).
    """
    await config_service.update_global_settings(global_settings)
    return global_settings

@router.post("/symbols/{symbol}", response_model=SymbolConfig)
async def update_symbol_config(symbol: str, symbol_config: SymbolConfig):
    """
    Updates the configuration for a specific symbol.
    """
    await config_service.update_symbol_config(symbol, symbol_config)
    return symbol_config
