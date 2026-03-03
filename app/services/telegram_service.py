import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.markdown import hbold, hcode

from app.core.settings import settings
from app.services.config_service import config_service

logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

from aiogram.types import WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """
    Handle /start command. Sends a welcome message and a button to open the Web App.
    """
    logger.info(f"User {message.from_user.id} in chat {message.chat.id} started the bot.")
    # Build robust URL
    base_url = settings.WEBAPP_URL.rstrip('/')
    if not base_url.endswith('/static/index.html'):
        webapp_url = f"{base_url}/static/index.html"
    else:
        webapp_url = base_url

    builder = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Открыть панель управления", web_app=WebAppInfo(url=webapp_url))]
        ],
        resize_keyboard=True
    )

    welcome_text = (
        f"👋 Привет! Я торговый робот.\n\n"
        f"Ваш Chat ID: {hcode(str(message.chat.id))}\n"
        f"Добавьте его в .env как {hcode('TELEGRAM_CHAT_ID')}, чтобы получать уведомления.\n\n"
        f"Нажми кнопку ниже, чтобы управлять настройками через Web App.\n"
    )
    await message.answer(welcome_text, reply_markup=builder, parse_mode="HTML")

@dp.message(Command("debug"))
async def cmd_debug(message: types.Message):
    """
    Debug command to check current settings.
    """
    debug_info = (
        f"🛠 <b>Debug Info:</b>\n"
        f"WEBAPP_URL: {hcode(settings.WEBAPP_URL)}\n"
        f"EXCHANGE: {hcode(settings.EXCHANGE_ID)}\n"
        f"TESTNET: {hcode(str(settings.USE_TESTNET))}\n"
    )
    await message.answer(debug_info, parse_mode="HTML")

async def send_message(text: str, chat_id: str = None):
    """
    Send a message to a specific chat or the default chat from settings.
    """
    target_chat_id = chat_id or settings.TELEGRAM_CHAT_ID
    if not target_chat_id:
        logger.warning("No TELEGRAM_CHAT_ID provided or set in settings. Cannot send message.")
        return False

    try:
        await bot.send_message(target_chat_id, text, parse_mode="HTML")
        return True
    except Exception as e:
        logger.error(f"Failed to send telegram message: {e}")
        return False

@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    """
    Handle /status command.
    """
    try:
        config = await config_service.get_config()
        if not config.symbols:
            await message.answer("⚠️ Конфигурация пуста или не загружена.")
            return

        status_lines = [
            hbold("📈 Текущий статус робота:"),
            f"Биржа: {hcode(config.settings.exchange_id.upper())}",
            f"Режим: {hcode('TESTNET' if config.settings.use_testnet else 'REAL MONEY')}\n"
        ]
        
        for symbol, data in config.symbols.items():
            status_emoji = "🟢" if data.status == "active" else "🟠" if data.status == "paused_for_entries" else "🔴"
            status_lines.append(
                f"{status_emoji} {hbold(symbol)}:\n"
                f"   Статус: {hcode(data.status)}\n"
                f"   Мультипликатор: {hcode(str(data.multiplier))}\n"
                f"   Плечо: {hcode(str(data.leverage))}x\n"
            )
        
        await message.answer("\n".join(status_lines), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error handling /status command: {e}")
        await message.answer("❌ Произошла ошибка при получении статуса.")

async def start_bot():
    """
    Start the bot polling.
    """
    logger.info("Starting Telegram Bot...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Telegram Bot Polling Error: {e}")

async def stop_bot():
    """
    Stop the bot.
    """
    logger.info("Stopping Telegram Bot...")
    await bot.session.close()
