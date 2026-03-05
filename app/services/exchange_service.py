import logging
import ccxt.async_support as ccxt
from app.core.settings import settings
from app.services.config_service import config_service

logger = logging.getLogger(__name__)

class ExchangeService:
    def __init__(self):
        self.exchange_id = None
        self.use_testnet = None
        self.client = None

    async def _get_client(self):
        """
        Lazily initializes the CCXT client based on the current config settings.
        Re-initializes if settings have changed.
        """
        config = await config_service.get_config()
        new_exchange_id = config.settings.exchange_id
        new_use_testnet = config.settings.use_testnet

        # Check if we need to re-initialize
        if (self.client is None or 
            self.exchange_id != new_exchange_id or 
            self.use_testnet != new_use_testnet):
            
            if self.client:
                await self.client.close()
            
            self.exchange_id = new_exchange_id
            self.use_testnet = new_use_testnet
            
            exchange_class = getattr(ccxt, self.exchange_id)
            
            # Common configuration
            client_config = {
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'swap',
                    'adjustForTimeDifference': True,
                    'recvWindow': 60000
                }
            }
            
            # Select credentials based on exchange
            if self.exchange_id == "okx":
                client_config.update({
                    'apiKey': settings.OKX_API_KEY,
                    'secret': settings.OKX_API_SECRET,
                    'password': settings.OKX_API_PASSPHRASE,
                })
            elif self.exchange_id == "bybit":
                client_config.update({
                    'apiKey': settings.BYBIT_API_KEY,
                    'secret': settings.BYBIT_API_SECRET,
                })
            elif self.exchange_id == "binance":
                client_config.update({
                    'apiKey': getattr(settings, 'BINANCE_API_KEY', ''),
                    'secret': getattr(settings, 'BINANCE_API_SECRET', ''),
                })
            # Add other exchanges as needed...

            self.client = exchange_class(client_config)
            
            # Set to testnet if configured
            if self.use_testnet:
                self.client.set_sandbox_mode(True)
                
            logger.info(f"CCXT {self.exchange_id} client initialized (Sandbox: {self.use_testnet})")
        
        return self.client

    async def close(self):
        if self.client:
            await self.client.close()
            self.client = None

    async def set_leverage(self, symbol: str, leverage: int):
        client = await self._get_client()
        ccxt_symbol = self._map_symbol(symbol)
        try:
            logger.info(f"CCXT {self.exchange_id}: Setting leverage for {ccxt_symbol} to {leverage}")
            return await client.set_leverage(leverage, ccxt_symbol)
        except Exception as e:
            logger.error(f"CCXT {self.exchange_id} API Error setting leverage: {e}")
            return None

    async def get_ticker(self, symbol: str):
        client = await self._get_client()
        ccxt_symbol = self._map_symbol(symbol)
        try:
            return await client.fetch_ticker(ccxt_symbol)
        except Exception as e:
            logger.error(f"CCXT {self.exchange_id} API Error fetching ticker: {e}")
            return None

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
            # CCXT handle symbols differently per exchange
            symbols = [self._map_symbol(symbol)] if symbol else None
            positions = await client.fetch_positions(symbols=symbols)
            return {"retCode": 0, "result": {"list": positions}}
        except Exception as e:
            logger.error(f"CCXT {self.exchange_id} API Error fetching positions: {e}")
            return {"retCode": -1, "retMsg": str(e)}

    async def get_balance(self):
        client = await self._get_client()
        try:
            # For Unified accounts on Bybit/OKX, we usually want the 'total' or 'USDT' balance
            balance = await client.fetch_balance()
            return {"retCode": 0, "result": balance}
        except Exception as e:
            logger.error(f"CCXT {self.exchange_id} API Error fetching balance: {e}")
            return {"retCode": -1, "retMsg": str(e)}

    def _map_symbol(self, symbol: str) -> str:
        """
        Maps simple symbols like 'BTCUSDT' to CCXT format.
        """
        if not symbol:
            return symbol
            
        # Strip .P suffix (TradingView Perpetual)
        if symbol.endswith(".P"):
            symbol = symbol.replace(".P", "")
            
        if "/" in symbol or "-" in symbol:
            return symbol
        
        if self.exchange_id == "okx":
            if symbol.endswith("USDT"):
                base = symbol.replace("USDT", "")
                return f"{base}-USDT-SWAP"
        
        # For Bybit and others, standard ETHUSDT usually works best with defaultType='swap'
        return symbol

exchange_service = ExchangeService()
