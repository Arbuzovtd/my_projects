import logging
import asyncio
from pybit.unified_trading import HTTP
from app.core.settings import settings

logger = logging.getLogger(__name__)

class BybitClient:
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = None):
        self.api_key = api_key or settings.BYBIT_API_KEY
        self.api_secret = api_secret or settings.BYBIT_API_SECRET
        self.testnet = testnet if testnet is not None else settings.USE_TESTNET
        
        try:
            self.session = HTTP(
                testnet=self.testnet,
                api_key=self.api_key,
                api_secret=self.api_secret,
            )
            logger.info("Bybit session initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Bybit session: {e}")
            raise

    async def get_wallet_balance(self, account_type: str = "UNIFIED", coin: str = None):
        try:
            response = await asyncio.to_thread(
                self.session.get_wallet_balance,
                accountType=account_type,
                coin=coin
            )
            return response
        except Exception as e:
            logger.error(f"Bybit API error in get_wallet_balance: {e}")
            return {"retCode": -1, "retMsg": str(e), "result": {}}

    async def place_order(self, *, category: str, symbol: str, side: str, order_type: str, qty: str, **kwargs):
        logger.info(f"Sending place_order request to Bybit: {symbol} {side} {qty}")
        try:
            response = await asyncio.to_thread(
                self.session.place_order,
                category=category,
                symbol=symbol,
                side=side,
                orderType=order_type,
                qty=qty,
                **kwargs
            )
            if response.get("retCode") == 0:
                logger.info(f"Bybit order success: {response.get('result')}")
            else:
                logger.error(f"Bybit order failure: {response.get('retCode')} - {response.get('retMsg')}")
            return response
        except Exception as e:
            logger.error(f"Unexpected Bybit API error in place_order: {e}")
            return {"retCode": -1, "retMsg": str(e), "result": {}}

    async def get_positions(self, category: str, symbol: str = None):
        try:
            params = {"category": category}
            if symbol:
                params["symbol"] = symbol
            response = await asyncio.to_thread(
                self.session.get_positions,
                **params
            )
            return response
        except Exception as e:
            logger.error(f"Unexpected Bybit API error in get_positions: {e}")
            return {"retCode": -1, "retMsg": str(e), "result": {}}

bybit_client = BybitClient()
