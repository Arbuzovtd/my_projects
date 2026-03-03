#!/bin/bash

echo "🚀 Starting Trading Bot Deployment..."

# 1. Проверяем наличие необходимых файлов
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found! Please create it from .env.example"
    exit 1
fi

if [ ! -f config.json ]; then
    echo "📝 Initializing empty config.json..."
    echo '{"settings": {"exchange_id": "bybit", "use_testnet": false}, "symbols": {}}' > config.json
fi

# 2. Создаем пустой файл БД, чтобы Docker правильно его примонтировал
touch config.db
touch bot.log

# 3. Пересобираем и запускаем контейнеры
echo "📦 Building and starting containers..."
docker compose down
docker compose up -d --build

echo "✅ Deployment finished! Bot is running in background."
echo "📜 To see logs: docker compose logs -f"
echo "🛠 To stop bot: docker compose down"
