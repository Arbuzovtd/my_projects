from typing import Dict, Literal
from pydantic import BaseModel, Field, RootModel, ConfigDict

class SymbolConfig(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "active",
                "multiplier": 10.0
            }
        }
    )
    status: Literal["active", "paused", "paused_for_entries"] = Field(
        ..., description="Trading status for the symbol"
    )
    multiplier: float = Field(
        ..., ge=0.0, description="Volume multiplier for USDT calculations"
    )

class AppConfig(RootModel):
    root: Dict[str, SymbolConfig]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "BTCUSDT": {
                    "status": "active",
                    "multiplier": 10.0
                },
                "ETHUSDT": {
                    "status": "paused_for_entries",
                    "multiplier": 5.0
                }
            }
        }
    )
