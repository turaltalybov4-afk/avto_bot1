# Template profile for a new client.
# 1) Copy this file to profiles/<client_slug>.py
# 2) Fill values
# 3) Run bot with AUTOBOT_PROFILE=<client_slug>

TOKEN = "PUT_BOT_TOKEN_HERE"
MANAGERS = [111111111]
DATABASE_FILE = "auto_client_slug.db"

COMPANY_NAME = "Название автосервиса"
TAGLINE = "Короткий слоган"
BUSINESS_HOURS = "Пн-Вс 09:00-21:00"
BUSINESS_FEATURES = [
    "Фишка 1",
    "Фишка 2",
    "Фишка 3",
]

WELCOME_TEXT = (
    "🚗 Добро пожаловать в {company_name}!\n\n"
   + "Подберем удобное время записи и покажем стоимость услуг."
)
RETURNING_WELCOME_TEXT = "👋 {name}, рады вас снова видеть! Выберите, что хотите сделать дальше."
BOOKING_INTRO_TEXT = "Выберите основную услугу для записи:"
CATALOG_TITLE = "📘 Каталог услуг"
NO_UPSELL_TEXT = "Для этой услуги дополнительных работ сейчас нет."

SERVICES = [
    {"name": "ТО", "price": 3000, "description": "Описание услуги"},
    {"name": "Диагностика", "price": 1800, "description": "Описание услуги"},
    {"name": "Ремонт", "price": 4500, "description": "Описание услуги"},
]

UPSELL = {
    "ТО": [
        {"name": "Замена фильтров", "price": 1000, "benefit": "Польза для клиента"},
        {"name": "Проверка свечей", "price": 700, "benefit": "Польза для клиента"},
    ],
    "Диагностика": [
        {"name": "Проверка тормозов", "price": 1200, "benefit": "Польза для клиента"}
    ],
}

BOOKING_DAYS_AHEAD = 5
TIMEZONE = "Asia/Krasnoyarsk"
TIME_SLOTS = ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"]
BOOKING_HOLD_MINUTES = 30
WEEKLY_REPORT_WEEKDAY = 0
WEEKLY_REPORT_HOUR = 9

MANAGER_NEW_BOOKING_TITLE = "📥 Новая запись"
MANAGER_HISTORY_TITLE = "📊 История клиента"
MANAGER_REVENUE_TITLE = "💰 Финансы клиента"
MANAGER_WEEKLY_REPORT_TITLE = "📈 Итоги за последнюю неделю"

REMINDER_24H_TEXT = "👋 Напоминаем о записи завтра в {time}. Будем рады вас видеть!"
REMINDER_2H_TEXT = "⏰ Напоминаем: запись сегодня в {time}. Подтвердите, пожалуйста, визит."
ABANDONED_BOOKING_TEXT = "👋 {name}, вы не закончили запись. Можем помочь подобрать удобное время."

BUTTON_BOOK = "🛠 Записаться"
BUTTON_CATALOG = "📘 Каталог услуг"
BUTTON_CONTACT_MANAGER = "📞 Связаться с менеджером"
BUTTON_MAIN_MENU = "🏠 Главное меню"
BUTTON_BACK_TO_BOOKING = "↩️ Вернуться к записи"
BUTTON_CONFIRM = "Подтвердить"
BUTTON_COMING = "✅ Приду"
BUTTON_CANCEL = "❌ Отменить"
BUTTON_RESCHEDULE = "🔁 Перенести"

CONTACT_MANAGER_TEXT = (
    "📞 Связь с менеджером\n\n"
   + "Напишите менеджеру: {manager_link}\n"
   + "ID менеджера: {manager_id}\n\n"
   + "Если хотите, можете также описать вопрос здесь в чате, и мы передадим его менеджеру."
)

MANAGER_CONTACT_REQUEST_TEXT = (
    "📞 Клиент запросил связь с менеджером\n"
   + "Клиент: {client_link}\n"
   + "ID: {client_id}\n"
   + "Username: {username}"
)
