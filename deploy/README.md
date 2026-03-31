# Деплой auto_bot на Linux VPS

Этот гайд работает для **любого Linux VPS**: Hetzner, DigitalOcean, Linode, AWS EC2, Scaleway и т.д.

## Что нужно

- Linux сервер с Ubuntu 20.04+ или Debian 11+
- SSH доступ от root
- Git установлен на сервере
- 2-4 GB RAM для 5 ботов

## Быстрый старт

### 1. Подключись к серверу

```bash
ssh root@IP_ТВОЕГО_СЕРВЕРА
```

### 2. Запусти установщик

```bash
git clone https://github.com/ТВОЙ_ЛОГИН/avto_bot1.git /tmp/setup_repo
bash /tmp/setup_repo/deploy/setup.sh
```

Установщик автоматически:
- Установит Python и зависимости
- Создаст виртуальное окружение
- Создаст системного пользователя `botuser`
- Зарегистрирует сервис systemd
- Создаст папки для данных

### 3. Отредактируй конфиг

```bash
nano /etc/auto_bot.env
```

Заполни значения:
```
BOT_TOKEN=ТВ_НОВЫЙ_ТОКЕН_ОТ_BOTFATHER
AUTOBOT_PROFILE=default
AUTOBOT_MANAGERS=ТВОЙ_TELEGRAM_ID
AUTOBOT_DATABASE_FILE=/var/lib/auto_bot/auto.db
```

Сохрани: `Ctrl+O`, `Enter`, `Ctrl+X`

### 4. Запусти бота

```bash
systemctl start autobot
systemctl enable autobot
systemctl status autobot
```

Если видишь `active (running)` — бот работает и будет автоматически подниматься после перезагрузки.

### 5. Проверь логи

```bash
journalctl -u autobot -f
```

## Запуск нескольких ботов на одном сервере

Для каждого бота создай отдельный сервис:

```bash
# Первый бот (дефолт)
systemctl start autobot
systemctl enable autobot

# Второй бот
BOT_USER=botuser2 BOT_DIR=/opt/auto_bot2 SERVICE_NAME=autobot2 bash /opt/auto_bot/deploy/setup.sh
nano /etc/auto_bot2.env       # заполни уникальный токен
systemctl start autobot2
systemctl enable autobot2

# Третий бот
BOT_USER=botuser3 BOT_DIR=/opt/auto_bot3 SERVICE_NAME=autobot3 bash /opt/auto_bot/deploy/setup.sh
nano /etc/auto_bot3.env
systemctl start autobot3
systemctl enable autobot3
```

Каждый сервис будет независимым: можно запускать, останавливать и перезагружать по отдельности.

## Полезные команды

```bash
# Статус всех ботов
systemctl status autobot*

# Логи конкретного бота
journalctl -u autobot -f
journalctl -u autobot2 -f
journalctl -u autobot3 -f

# Перезагрузить бота
systemctl restart autobot

# Остановить бота
systemctl stop autobot

# Отключить автозапуск
systemctl disable autobot

# Удалить сервис
systemctl stop autobot
systemctl disable autobot
rm /etc/systemd/system/autobot.service
systemctl daemon-reload
```

## Где хранятся данные

- Код проекта: `/opt/auto_bot`
- База данных SQLite: `/var/lib/auto_bot/auto.db`
- Конфиг с токенами: `/etc/auto_bot.env`
- Логи: `journalctl -u autobot`

## Обновление кода с GitHub

```bash
cd /opt/auto_bot
git pull origin main
systemctl restart autobot
```

## Настройка виртуального окружения

Если нужны свои переменные, отредактируй `/etc/auto_bot.env`:

```bash
nano /etc/auto_bot.env
```

Доступные переменные:

```
BOT_TOKEN              # Токен Telegram бота (обязателен)
AUTOBOT_PROFILE        # default или другой профиль из profiles/
AUTOBOT_MANAGERS       # Telegram ID менеджеров (можно несколько через запятую)
AUTOBOT_DATABASE_FILE  # Путь к базе данных
AUTOBOT_BOOKING_HOLD_MINUTES  # Минуты удержания брони (по умолч 30)
AUTOBOT_WEEKLY_REPORT_WEEKDAY # День недели для отчёта (0 = понедельник)
AUTOBOT_WEEKLY_REPORT_HOUR    # Час отправки отчёта (0-23)
```

После редактирования перезагрузи сервис:

```bash
systemctl restart autobot
```

## Troubleshooting

### Сервис не запускается

```bash
journalctl -u autobot -n 50
```

Посмотри в логах ошибку и исправь в конфиге.

### "Ошибка подключения к токену"

Токен неверный. Перейди в BotFather (@BotFather в Telegram), выбери своего бота и получи новый токен. Вставь в `/etc/auto_bot.env` и перезапусти:

```bash
nano /etc/auto_bot.env
systemctl restart autobot
```

### "База данных заблокирована"

SQLite иногда конфликтует. Просто перезагрузи сервис:

```bash
systemctl restart autobot
```

### Использование диска растёт

Логи в journalctl занимают место. Почистить можно:

```bash
journalctl --vacuum=100M
```

## Для разных провайдеров VPS

### Hetzner Cloud
1. Создай сервер (CX22 за €4.49/месяц)
2. Выбери Ubuntu 24.04
3. Получишь IP и пароль root
4. Подключись: `ssh root@IP`
5. Выполни инструкцию выше

### DigitalOcean
1. Создай дроплет (забрось монету - подойдёт любой за $4-6/месяц)
2. Выбери Ubuntu 24.04
3. Получишь IP
4. Подключись: `ssh root@IP`
5. Выполни инструкцию выше

### Linode
1. Создай Linode (Nanode $5/месяц подойдёт)
2. Ubuntu 24.04
3. Получишь IP и рут пароль
4. Подключись и выполни инструкцию

### AWS EC2
1. Запусти инстанс (t2.micro подойдёт)
2. Ubuntu 24.04 AMI
3. Security Group открой порт 22 для SSH
4. Подключись через SSH
5. Выполни инструкцию

Во всех случаях процесс одинаков: подключиться по SSH → запустить setup.sh → готово.

## Хотел бы большше помощи?

Если возникли проблемы, в логах обычно всё понятно:

```bash
journalctl -u autobot -n 100
```

Ошибка будет видна в выводе. Потом можно её погуглить или попросить помощь.
