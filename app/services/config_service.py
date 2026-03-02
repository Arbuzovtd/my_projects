import json
import asyncio
import logging
from typing import Optional, Dict, Any
from app.models.config import AppConfig, SymbolConfig, GlobalSettings
from app.core.settings import settings

logger = logging.getLogger(__name__)

class ConfigService:
    def __init__(self, config_path: str = None):
        self._config_path = config_path
        self._lock = asyncio.Lock()

    @property
    def config_path(self) -> str:
        return self._config_path or settings.CONFIG_PATH

    async def get_config(self) -> AppConfig:
        """
        Public method to read config with an async lock.
        """
        async with self._lock:
            return await self._read_config_internal()

    async def save_config(self, config: AppConfig):
        """
        Public method to save config with an async lock.
        """
        async with self._lock:
            await self._write_config_internal(config)

    async def update_symbol_config(self, symbol: str, symbol_config: SymbolConfig):
        """
        Updates config for a specific symbol using an async lock.
        """
        async with self._lock:
            config = await self._read_config_internal()
            config.symbols[symbol] = symbol_config
            await self._write_config_internal(config)
            logger.info(f"Symbol config for {symbol} updated and saved.")

    async def update_global_settings(self, global_settings: GlobalSettings):
        """
        Updates global settings using an async lock.
        """
        async with self._lock:
            config = await self._read_config_internal()
            config.settings = global_settings
            await self._write_config_internal(config)
            logger.info("Global settings updated and saved.")

    async def _read_config_internal(self) -> AppConfig:
        """
        Internal method to read config file. Handles migration from old RootModel format.
        """
        try:
            data = await asyncio.to_thread(self._read_file_sync)
            if data is None:
                return AppConfig()
            
            # Migration logic
            if "symbols" not in data and "settings" not in data:
                # Old format was just RootModel[Dict[str, SymbolConfig]]
                logger.info("Migrating old config format...")
                return AppConfig(symbols=data)
            
            return AppConfig.model_validate(data)
        except Exception as e:
            logger.error(f"Error reading config internal: {e}")
            return AppConfig()

    async def _write_config_internal(self, config: AppConfig):
        """
        Internal method to write config file. Not thread-safe on its own.
        """
        try:
            await asyncio.to_thread(self._write_file_sync, config.model_dump())
        except Exception as e:
            logger.error(f"Error writing config internal: {e}")
            raise

    def _read_file_sync(self) -> Optional[Dict[str, Any]]:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def _write_file_sync(self, data: Dict[str, Any]):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

# Singleton instance
config_service = ConfigService()
