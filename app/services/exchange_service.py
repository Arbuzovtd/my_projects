import logging
import ccxt.async_support as ccxt
from app.core.settings import settings

logger = logging.getLogger(__name__)

class ExchangeService:
    def __init__(self):
        self.exchange_id = settings.EXCHANGE_ID
        self.client = None

    async def _get_client(self):
        """
        Lazily initializes the CCXT client based on the EXCHANGE_ID in settings.
        """
        if self.client is None:
            exchange_class = getattr(ccxt, self.exchange_id)
            
            # Common configuration
            config = {
                'enableRateLimit': True,
                'options': {'defaultType': 'swap' if self.exchange_id == 'okx' else 'future'}
            }
            
            # Select credentials based on exchange
            if self.exchange_id == "okx":
                config.update({
                    'apiKey': settings.OKX_API_KEY,
                    'secret': settings.OKX_API_SECRET,
                    'password': settings.OKX_API_PASSPHRASE,
                })
            elif self.exchange_id == "bybit":
                config.update({
                    'apiKey': settings.BYBIT_API_KEY,
                    'secret': settings.BYBIT_API_SECRET,
                })
            # Add other exchanges as needed...

            self.client = exchange_class(config)
            
            # Set to testnet if configured
            if settings.USE_TESTNET:
                self.client.set_sandbox_mode(True)
                
            logger.info(f"CCXT {self.exchange_id} client initialized (Sandbox: {settings.USE_TESTNET})")
        
        return self.client

    async def close(self):
        if self.client:
            await self.client.close()
            self.client = None

    async def create_market_order(self, symbol: str, side: str, amount: float, params: dict = None):
        client = await self._get_client()
        ccxt_symbol = self._map_symbol(symbol)
        
        logger.info(f"CCXT {self.exchange_id}: Placing market {side} order for {ccxt_symbol}, amount={amount}")
        try:
            order = await client.create_market_order(
                symbol=ccxt_symbol,
                side=side.lower(),
                amount=amount,
                params=params or {}
            )
            return {"retCode": 0, "result": order}
        except Exception as e:
            logger.error(f"CCXT {self.exchange_id} API Error: {e}")
            return {"retCode": -1, "retMsg": str(e)}

    async def get_positions(self, symbol: str = None):
        client = await self._get_client()
        try:
            # For OKX, fetch_positions returns all positions if symbols is None
            symbols = [self._map_symbol(symbol)] if symbol else None
            positions = await client.fetch_positions(symbols=symbols)
            return {"retCode": 0, "result": {"list": positions}}
        except Exception as e:
            logger.error(f"CCXT {self.exchange_id} API Error fetching positions: {e}")
            return {"retCode": -1, "retMsg": str(e)}

    def _map_symbol(self, symbol: str) -> str:
        """
        Maps simple symbols like 'BTCUSDT' to CCXT format like 'BTC/USDT:USDT' (Bybit/Binance) or 'BTC-USDT-SWAP' (OKX).
        """
        if "/" in symbol or "-" in symbol:
            return symbol
        
        # Mapping logic for OKX Perpetual Swap
        if self.exchange_id == "okx":
            if symbol.endswith("USDT"):
                base = symbol.replace("USDT", "")
                return f"{base}-USDT-SWAP"
        
        # Mapping logic for Bybit/Binance Futures
        if symbol.endswith("USDT"):
            base = symbol.replace("USDT", "")
            return f"{base}/USDT:USDT"
        
        return symbol

exchange_service = ExchangeService()
