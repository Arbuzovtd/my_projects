from fastapi import APIRouter, HTTPException, Depends
from typing import Dict
from app.models.config import AppConfig, SymbolConfig
from app.services.config_service import config_service

router = APIRouter(prefix="/api/config", tags=["config"])

@router.get("/", response_model=Dict[str, SymbolConfig])
async def get_config():
    """
    Returns the current application configuration for symbols.
    """
    config = await config_service.get_config()
    return config.root

@router.post("/{symbol}", response_model=SymbolConfig)
async def update_symbol_config(symbol: str, symbol_config: SymbolConfig):
    """
    Updates the configuration for a specific symbol.
    """
    await config_service.update_symbol_config(symbol, symbol_config)
    return symbol_config
