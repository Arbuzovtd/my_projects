# Trading Bot: TV Webhook to Exchange

Этот бот принимает сигналы от TradingView (через Webhook) и автоматически открывает/закрывает позиции на биржах (Bybit, OKX, Binance) через CCXT. В комплекте идет WebApp для управления настройками прямо из Telegram.

## 🚀 Быстрый старт (Локально)

Для управления зависимостями используется [uv](https://github.com/astral-sh/uv).

1. **Клонируйте репозиторий и перейдите в папку:**
   ```bash
   git clone <repo_url>
   cd test_auto_dev
   ```

2. **Настройте переменные окружения:**
   Скопируйте пример конфига и впишите свои API ключи:
   ```bash
   cp .env.example .env # Если файла нет, создайте его на основе описания ниже
   ```

3. **Запустите бота:**
   ```bash
   uv run python main.py
   ```
   Бот запустится на `http://localhost:8000`. WebApp будет доступен по адресу `http://localhost:8000/static/index.html`.

## ⚙️ Настройка (.env)

| Ключ | Описание |
|------|----------|
| `WEBHOOK_PASSPHRASE` | Секретное слово для защиты вебхука (укажите его в TradingView). |
| `BYBIT_API_KEY` / `SECRET` | Ключи от Bybit. |
| `OKX_API_KEY` / `SECRET` / `PASSPHRASE` | Ключи от OKX. |
| `TELEGRAM_BOT_TOKEN` | Токен вашего бота из @BotFather. |
| `TELEGRAM_CHAT_ID` | Ваш ID (узнать можно у @userinfobot). |

## 🧪 Тестирование

### Автоматические тесты
Для проверки корректности логики (конфиги, расчеты, API):
```bash
uv run pytest
```

### Имитация сигнала TradingView
Чтобы проверить связь с биржей (например, Bybit на реальных деньгах), используйте скрипт:
```bash
# Формат: uv run python send_test_signal.py <action> <ticker> <side> <qty>
uv run python send_test_signal.py entry BTCUSDT long 0.001
```

## 🌐 Развертывание на сервере (Docker)

Для работы 24/7 рекомендуется использовать Docker Compose.

1. **Установите Docker и Docker Compose на сервер.**
2. **Загрузите файлы проекта и настройте `.env`.**
3. **Запустите контейнеры:**
   ```bash
   docker-compose up -d --build
   ```
4. **Настройте Nginx (опционально):** Для доступа по HTTPS (требуется для TradingView) используйте Nginx + Certbot.

## 📈 Настройка TradingView

При создании Alert в TradingView:
1. **Webhook URL:** `http://ваш-ip:8000/webhook` (или ваш домен).
2. **Message (JSON):**
   ```json
   {
     "passphrase": "ваш_секрет",
     "ticker": "{{ticker}}",
     "action": "entry",
     "side": "{{strategy.order.action}}",
     "qty": 0.01
   }
   ```

## 📱 WebApp в Telegram
Для удобного управления:
1. Зайдите в WebApp через вашего бота.
2. В разделе **Global Settings** выберите биржу и режим (Testnet/Real).
3. Для каждого тикера настройте **Multiplier** (множитель объема) и **Leverage** (плечо).
