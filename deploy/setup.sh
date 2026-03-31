#!/bin/bash
# Скрипт установки auto_bot на любой Linux VPS (Ubuntu/Debian)
# Запускать от root: bash setup.sh

set -e

# Параметры установки (можно менять)
BOT_DIR="${BOT_DIR:-/opt/auto_bot}"
BOT_USER="${BOT_USER:-botuser}"
BOT_DATA_DIR="${BOT_DATA_DIR:-/var/lib/auto_bot}"
BOT_ENV_FILE="${BOT_ENV_FILE:-/etc/auto_bot.env}"
SERVICE_NAME="${SERVICE_NAME:-autobot}"

echo "== Универсальный установщик auto_bot =="
echo ""
echo "Директория проекта: $BOT_DIR"
echo "Системный пользователь: $BOT_USER"
echo "Папка данных: $BOT_DATA_DIR"
echo "Файл конфига: $BOT_ENV_FILE"
echo ""

echo "==> Обновляем пакеты и ставим зависимости..."
apt-get update -y
apt-get install -y python3 python3-pip python3-venv git

echo ""
echo "==> Создаём системного пользователя $BOT_USER..."
if ! id "$BOT_USER" &>/dev/null; then
    useradd --system --no-create-home --shell /usr/sbin/nologin "$BOT_USER"
    echo "✓ Пользователь $BOT_USER создан"
else
    echo "✓ Пользователь $BOT_USER уже существует"
fi

echo ""
echo "==> Клонируем или обновляем репозиторий..."
if [ -d "$BOT_DIR/.git" ]; then
    git -C "$BOT_DIR" pull
    echo "✓ Репозиторий обновлен"
else
    read -p "Введи ссылку на GitHub репозиторий (https://github.com/...): " REPO_URL
    git clone "$REPO_URL" "$BOT_DIR"
    echo "✓ Репозиторий клонирован"
fi

echo ""
echo "==> Создаём виртуальное окружение и ставим Python-зависимости..."
python3 -m venv "$BOT_DIR/.venv"
"$BOT_DIR/.venv/bin/pip" install --upgrade pip setuptools wheel
"$BOT_DIR/.venv/bin/pip" install -r "$BOT_DIR/requirements.txt"
echo "✓ Зависимости установлены"

echo ""
echo "==> Создаём папку для базы данных..."
mkdir -p "$BOT_DATA_DIR"
chown "$BOT_USER":"$BOT_USER" "$BOT_DATA_DIR"
chmod 750 "$BOT_DATA_DIR"
echo "✓ Папка $BOT_DATA_DIR создана"

echo ""
echo "==> Копируем systemd unit-файл..."
cp "$BOT_DIR/deploy/autobot.service" "/etc/systemd/system/${SERVICE_NAME}.service"
sed -i "s|SETUP_BOT_DIR|$BOT_DIR|g" "/etc/systemd/system/${SERVICE_NAME}.service"
sed -i "s|SETUP_BOT_USER|$BOT_USER|g" "/etc/systemd/system/${SERVICE_NAME}.service"
sed -i "s|SETUP_BOT_ENV_FILE|$BOT_ENV_FILE|g" "/etc/systemd/system/${SERVICE_NAME}.service"
systemctl daemon-reload
echo "✓ Сервис $SERVICE_NAME зарегистрирован"

echo ""
echo "==> Проверяем наличие файла конфига..."
if [ ! -f "$BOT_ENV_FILE" ]; then
    cat > "$BOT_ENV_FILE" << 'EOF'
# Файл конфигурации для auto_bot
# Заполни эти значения перед запуском сервиса

BOT_TOKEN=PUT_NEW_BOT_TOKEN_HERE
AUTOBOT_PROFILE=default
AUTOBOT_MANAGERS=111111111
AUTOBOT_DATABASE_FILE=/var/lib/auto_bot/auto.db
EOF
    chmod 600 "$BOT_ENV_FILE"
    chown "$BOT_USER":"$BOT_USER" "$BOT_ENV_FILE"
    echo "✓ Создан файл конфига: $BOT_ENV_FILE"
else
    echo "✓ Файл конфига уже существует: $BOT_ENV_FILE"
fi

echo ""
echo "======================================"
echo "   Установка завершена успешно!"
echo "======================================"
echo ""
echo "Что делать дальше:"
echo ""
echo "1. Отредактируй файл конфига:"
echo "   nano $BOT_ENV_FILE"
echo ""
echo "   Необходимо заполнить:"
echo "   - BOT_TOKEN: новый токен от BotFather"
echo "   - AUTOBOT_MANAGERS: твой Telegram ID (узнай через @userinfobot)"
echo ""
echo "2. Запусти сервис:"
echo "   systemctl start $SERVICE_NAME"
echo ""
echo "3. Проверь статус:"
echo "   systemctl status $SERVICE_NAME"
echo ""
echo "4. Включи автозапуск:"
echo "   systemctl enable $SERVICE_NAME"
echo ""
echo "Логи можно смотреть:"
echo "   journalctl -u $SERVICE_NAME -f"
