from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Security
    WEBHOOK_PASSPHRASE: str = "default_secret"
    
    # Exchange Selection
    EXCHANGE_ID: str = "okx" # 'bybit', 'okx', 'binance', etc.
    USE_TESTNET: bool = True
    
    # Bybit Credentials
    BYBIT_API_KEY: str = ""
    BYBIT_API_SECRET: str = ""
    
    # OKX Credentials
    OKX_API_KEY: str = ""
    OKX_API_SECRET: str = ""
    OKX_API_PASSPHRASE: str = ""
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    WEBAPP_URL: str = "http://localhost:8000"
    
    # App Settings
    CONFIG_PATH: str = "config.json"
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "bot.log"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
