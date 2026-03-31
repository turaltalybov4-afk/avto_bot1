#!/bin/bash
# Скрипт установки auto_bot на Ubuntu / Debian VPS (Hetzner)
# Запускать от root: bash setup.sh

set -e

BOT_DIR="/opt/auto_bot"
BOT_USER="botuser"

echo "==> Обновляем пакеты и ставим зависимости..."
apt-get update -y
apt-get install -y python3 python3-pip python3-venv git

echo "==> Создаём системного пользователя $BOT_USER..."
if ! id "$BOT_USER" &>/dev/null; then
    useradd --system --no-create-home --shell /usr/sbin/nologin "$BOT_USER"
fi

echo "==> Клонируем или обновляем репозиторий..."
if [ -d "$BOT_DIR/.git" ]; then
    git -C "$BOT_DIR" pull
else
    read -p "Вставь ссылку на твой GitHub репозиторий (https://github.com/...): " REPO_URL
    git clone "$REPO_URL" "$BOT_DIR"
fi

echo "==> Создаём виртуальное окружение и ставим зависимости Python..."
python3 -m venv "$BOT_DIR/.venv"
"$BOT_DIR/.venv/bin/pip" install --upgrade pip
"$BOT_DIR/.venv/bin/pip" install -r "$BOT_DIR/requirements.txt"

echo "==> Создаём папку для базы данных..."
mkdir -p /var/lib/auto_bot
chown "$BOT_USER":"$BOT_USER" /var/lib/auto_bot

echo "==> Копируем systemd unit-файл..."
cp "$BOT_DIR/deploy/autobot.service" /etc/systemd/system/autobot.service
systemctl daemon-reload

echo ""
echo "==> Готово. Теперь создай файл с секретами:"
echo "    nano /etc/auto_bot.env"
echo ""
echo "    Вставь в него:"
echo "    BOT_TOKEN=твой_токен_бота"
echo "    AUTOBOT_PROFILE=default"
echo "    AUTOBOT_MANAGERS=твой_telegram_id"
echo "    AUTOBOT_DATABASE_FILE=/var/lib/auto_bot/auto.db"
echo ""
echo "    Потом запусти:"
echo "    systemctl enable autobot"
echo "    systemctl start autobot"
echo "    systemctl status autobot"
