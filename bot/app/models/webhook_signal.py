from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class WebhookSignal(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "passphrase": "your_secret_passphrase",
                "ticker": "BTCUSDT",
                "action": "entry",
                "side": "long",
                "qty": 1.0
            }
        }
    )
    passphrase: str = Field(..., description="Secret token for security")
    ticker: str = Field(..., description="Trading pair symbol (e.g., BTCUSDT)")
    action: Literal["entry", "close_all"] = Field(..., description="Type of signal")
    side: Literal["long", "short"] = Field(..., description="Side of the trade")
    qty: float = Field(0.0, description="Quantity in base units (for entry/averaging)")
