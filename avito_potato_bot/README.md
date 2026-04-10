# Avito Potato Bot (isolated)

Этот бот сделан отдельно от ваших текущих ботов и не меняет их код.

## Что умеет

- Отвечает на частые вопросы:
  - цена
  - сколько кг в мешке
  - когда доставка
- Понимает разные формулировки через нормализацию текста.
- Ведет клиента к заказу и собирает:
  - количество
  - день доставки
  - окно доставки (днем/вечером после обеда)
  - адрес
  - подъезд/этаж
  - телефон
  - комментарий
- Сохраняет заявку в SQLite.
- Шлет заявку менеджеру в Telegram.

## Быстрый старт

1. Откройте папку `avito_potato_bot`.
2. Скопируйте `config.example.json` в `config.json`.
3. Заполните:
   - `telegram_bot_token`
   - `telegram_manager_chat_id`
   - `avito_access_token` (для вашего адаптера Avito)
4. Установите зависимости:

```powershell
pip install -r requirements.txt
```

5. Запустите сервер:

```powershell
uvicorn app:APP --host 0.0.0.0 --port 8088
```

## Как подключать к Avito

В этом MVP endpoint:

- `POST /webhook/incoming`

Принимает JSON:

```json
{
  "chat_id": "avito_chat_123",
  "client_id": "user_987",
  "client_name": "Иван",
  "text": "Сколько кг в мешке?"
}
```

Возвращает JSON:

```json
{
  "reply_text": "В одном мешке обычно 25 кг. Если хотите, могу сразу оформить заказ."
}
```

Дальше ваш Avito-адаптер должен:

1. Передавать входящие сообщения сюда.
2. Брать `reply_text` из ответа.
3. Отправлять его обратно в диалог Avito через API.

## Проверка локально

```powershell
curl -X POST http://127.0.0.1:8088/webhook/incoming `
  -H "Content-Type: application/json" `
  -d '{"chat_id":"1","client_id":"u1","client_name":"Петр","text":"Сколько стоит картошка?"}'
```

## Где заявки

- БД: `avito_potato_bot/avito_potato.db`
- Таблица: `leads`

## Примечание

Этот модуль специально изолирован. Ваши файлы `main.py`, `config.py`, `database.py` не затронуты.
