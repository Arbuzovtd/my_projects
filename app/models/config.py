from typing import Dict, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict

class GlobalSettings(BaseModel):
    exchange_id: str = Field("okx", description="Active exchange (bybit, okx, binance)")
    use_testnet: bool = Field(True, description="Whether to use exchange sandbox/testnet")

class SymbolConfig(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "active",
                "multiplier": 10.0,
                "leverage": 5
            }
        }
    )
    status: Literal["active", "paused", "paused_for_entries"] = Field(
        ..., description="Trading status for the symbol"
    )
    multiplier: float = Field(
        ..., ge=0.0, description="Volume multiplier for USDT calculations"
    )
    leverage: int = Field(
        default=1, ge=1, le=125, description="Leverage for the symbol"
    )

class AppConfig(BaseModel):
    settings: GlobalSettings = Field(default_factory=GlobalSettings)
    symbols: Dict[str, SymbolConfig] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "settings": {
                    "exchange_id": "okx",
                    "use_testnet": True
                },
                "symbols": {
                    "BTCUSDT": {
                        "status": "active",
                        "multiplier": 10.0,
                        "leverage": 10
                    }
                }
            }
        }
    )
