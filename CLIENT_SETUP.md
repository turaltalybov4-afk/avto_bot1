# Как использовать один код для многих клиентов

## 1) Создать файл профиля
1. Скопируйте `profiles/template_client.py` в `profiles/<client_slug>.py`.
2. Заполните поля в новом файле:
- TOKEN
- MANAGERS
- COMPANY_NAME
- BUSINESS_HOURS
- SERVICES
- UPSELL
- тексты и кнопки при необходимости

## 2) Запуск с выбранным профилем клиента
Используйте переменную окружения `AUTOBOT_PROFILE`.

Пример для PowerShell:

```powershell
$env:AUTOBOT_PROFILE = "client_slug"
.\.venv\Scripts\python.exe .\main.py
```

Если `AUTOBOT_PROFILE` не задан, бот использует `profiles/default.py`.

## Реальный пример
В проект уже добавлен пример профиля:

- `profiles/turbo_service.py`

Запуск этого примера:

```powershell
$env:AUTOBOT_PROFILE = "turbo_service"
.\.venv\Scripts\python.exe .\main.py
```

Важно:
- в файле `profiles/turbo_service.py` нужно заменить `TOKEN` на реальный токен бота
- и `MANAGERS` на реальные Telegram ID менеджеров
- у профиля своя база: `auto_turbo_service.db`

## 3) Что менять для каждого клиента
- `SERVICES`: основные услуги и их цены
- `UPSELL`: дополнительные услуги для каждой основной услуги
- `TIME_SLOTS` и `BOOKING_DAYS_AHEAD`
- `BUSINESS_HOURS`, `BUSINESS_FEATURES`, `TAGLINE`
- `DATABASE_FILE`: отдельная база данных для конкретного клиента
- шаблоны сообщений и подписи кнопок

## 4) Как удобно масштабировать
- Держите одну git-ветку с шаблоном (`profiles/default.py`).
- Для каждого нового клиента создавайте только один новый файл профиля в `profiles/`.
- Не меняйте `main.py` под каждого клиента, если не нужна новая бизнес-логика.

## 5) Можно ли запускать и останавливать ботов по отдельности
Да, можно.

Как это работает:
- у каждого клиента свой профиль
- у каждого клиента свой токен бота
- у каждого клиента может быть своя база данных через `DATABASE_FILE`
- значит, каждый бот запускается как отдельный процесс

Пример:

```powershell
$env:AUTOBOT_PROFILE = "turbo_service"
.\.venv\Scripts\python.exe .\main.py
```

В другом окне PowerShell можно запустить другого клиента:

```powershell
$env:AUTOBOT_PROFILE = "client_b"
.\.venv\Scripts\python.exe .\main.py
```

То есть:
- можно запустить одного бота
- можно запустить двух и более одновременно
- можно остановить только одного, закрыв именно его окно терминала или завершив именно его процесс

Если у двух профилей разные токены, они не мешают друг другу.
Если у двух профилей один и тот же токен, Telegram даст ошибку `Conflict`.
