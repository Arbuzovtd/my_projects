import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.webhook import router as webhook_router
from app.api.config import router as config_router
from app.services.telegram_service import start_bot, stop_bot
from app.core.logging_config import setup_logging

# Initialize logging before creating the app
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Trade Bot application...")
    # Startup: Start Telegram bot as a background task
    bot_task = asyncio.create_task(start_bot())
    yield
    # Shutdown: Stop Telegram bot
    logger.info("Shutting down Trade Bot application...")
    await stop_bot()
    bot_task.cancel()
    try:
        await bot_task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="Auto Dev Trade Bot", version="0.1.0", lifespan=lifespan)

app.include_router(webhook_router)
app.include_router(config_router)

# Mount static files for the Telegram WebApp
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def root():
    return {"message": "Hello from test-auto-dev FastAPI server"}
