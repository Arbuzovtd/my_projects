#!/bin/bash

# Скрипт автоматической настройки сервера для торгового бота (HTTPS + Basic Auth)
# Домен: mytradebot0kx.ru
# Почта: timkzn04@gmail.com

set -e

echo "🚀 Начинаем настройку сервера для mytradebot0kx.ru..."

# 1. Обновление системы
echo "🔄 Обновление системных пакетов..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Установка Docker
if ! command -v docker &> /dev/null; then
    echo "🐳 Установка Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "✅ Docker установлен успешно."
else
    echo "✅ Docker уже установлен."
fi

# 3. Создание рабочей директории
PROJECT_DIR="/root/trade_bot"
echo "📁 Создание директории проекта: $PROJECT_DIR"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 4. Настройка логина и пароля для входа в панель
echo "--------------------------------------------------"
echo "🔐 ПРИДУМАЙТЕ ДАННЫЕ ДЛЯ ВХОДА В ВАШУ ПАНЕЛЬ"
echo "--------------------------------------------------"
read -p "Придумайте ЛОГИН для входа в панель (например, admin): " ADMIN_USER
read -s -p "Придумайте ПАРОЛЬ для входа в панель: " ADMIN_PASS
echo -e "\n--------------------------------------------------"

# Генерация хеша пароля для Caddy (через временный контейнер caddy)
echo "🔑 Генерируем безопасный хеш пароля..."
HASHED_PASS=$(docker run --rm caddy caddy hash-password --plaintext "$ADMIN_PASS")

# 5. Создание Caddyfile
echo "📝 Создание Caddyfile (SSL + Basic Auth)..."
cat <<EOF > Caddyfile
{
    email timkzn04@gmail.com
}

mytradebot0kx.ru {
    # Защита всей панели логином и паролем
    basicauth /static/* {
        $ADMIN_USER $HASHED_PASS
    }
    # Защита API (настроек) логином и паролем
    basicauth /api/* {
        $ADMIN_USER $HASHED_PASS
    }

    reverse_proxy trading-bot:8000
}
EOF

# 6. Создание docker-compose.yml
echo "📝 Создание docker-compose.yml..."
cat <<EOF > docker-compose.yml
services:
  trading-bot:
    image: timurarbuzov/trading-bot:latest
    container_name: trading-bot
    restart: unless-stopped
    env_file:
      - .env
    expose:
      - "8000"
    volumes:
      - ./config.json:/app/config.json
      - ./config.db:/app/config.db
      - ./bot.log:/app/bot.log
    logging:
      driver: "json-file"
      options:
        max-size: "10mb"
        max-file: "3"

  caddy:
    image: caddy:latest
    container_name: caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config

volumes:
  caddy_data:
  caddy_config:
EOF

# 7. Создание пустых файлов конфигурации (чтобы Docker не создал папки)
echo "📝 Создание файлов данных..."
touch config.db bot.log
if [ ! -f config.json ]; then
    echo "{}" > config.json
fi

# 8. Создание .env.example
echo "📝 Создание .env.example..."
cat <<EOF > .env.example
# --- Bybit API Configuration ---
BYBIT_API_KEY=your_api_key_here
BYBIT_API_SECRET=your_api_secret_here
BYBIT_TESTNET=true

# --- Telegram Bot Configuration ---
TELEGRAM_BOT_TOKEN=your_bot_token_here
# Можно указать несколько ID через запятую: 12345678, 87654321
TELEGRAM_CHAT_ID=12345678
WEBAPP_URL=https://mytradebot0kx.ru

# --- Security ---
WEBHOOK_PASSPHRASE=your_secret_passphrase_here

# --- App Settings ---
EXCHANGE_ID=bybit
USE_TESTNET=true
LOG_LEVEL=INFO
EOF

echo "--------------------------------------------------"
echo "✅ Настройка завершена успешно!"
echo "--------------------------------------------------"
echo "Ваши следующие шаги:"
echo "1. Выполните: cd $PROJECT_DIR"
echo "2. Создайте .env: cp .env.example .env"
echo "3. Отредактируйте .env: nano .env (вставьте ваши реальные ключи)"
echo "4. Запустите бота: docker compose pull && docker compose up -d"
echo "--------------------------------------------------"
echo "👤 Ваш логин для панели: $ADMIN_USER"
echo "🔗 Адрес панели: https://mytradebot0kx.ru/static/index.html"
echo "--------------------------------------------------"
