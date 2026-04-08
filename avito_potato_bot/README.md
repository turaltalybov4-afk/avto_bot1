# Avito Potato Bot (isolated)

Этот модуль отдельный и не вмешивается в ваши текущие боты.

## Что делает

- Отвечает на FAQ:
  - цена
  - сколько кг в мешке
  - когда доставка
- Понимает разные формулировки за счет нормализации текста.
- Ведет клиента к заказу и пошагово собирает:
  - количество мешков
  - день доставки
  - окно доставки (днем/вечером после обеда)
  - адрес
  - подъезд/этаж
  - телефон
  - комментарий
- Сохраняет заявку в SQLite.
- Отправляет заявку в Telegram менеджеру.

## Быстрый запуск

1. Перейдите в папку:

```powershell
cd .\avito_potato_bot
```

2. Скопируйте конфиг:

```powershell
Copy-Item .\config.example.json .\config.json
```

3. Заполните в config.json:
- telegram_bot_token
- telegram_manager_chat_id

4. Установите зависимости:

```powershell
pip install -r requirements.txt
```

5. Запустите сервер:

```powershell
uvicorn app:APP --host 0.0.0.0 --port 8088
```

## Как подключить к Avito

Endpoint для входящих сообщений:

- POST /webhook/incoming

Формат входящего JSON:

```json
{
  "chat_id": "avito_chat_123",
  "client_id": "avito_user_42",
  "client_name": "Иван",
  "text": "Сколько кг в мешке?"
}
```

Ответ:

```json
{
  "reply_text": "Обычно в одном мешке 25 кг. Если хотите, могу сразу оформить заказ."
}
```

Ваш интеграционный слой Avito должен:

1. Получить входящее сообщение из Avito.
2. Передать его в этот endpoint.
3. Взять reply_text из ответа.
4. Отправить reply_text обратно клиенту в чат Avito.

## Локальная проверка

```powershell
curl -X POST http://127.0.0.1:8088/webhook/incoming `
  -H "Content-Type: application/json" `
  -d '{"chat_id":"1","client_id":"u1","client_name":"Петр","text":"Сколько стоит картошка?"}'
```

## Где хранится

- БД: avito_potato.db
- Заявки: таблица leads
- Текущие диалоги: таблица sessions
