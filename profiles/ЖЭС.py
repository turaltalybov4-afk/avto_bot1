
TOKEN = "8743852204:AAE0fJxVnGgbsF-Ts_p704bYwuXJA2rcOmw"
MANAGERS = [6271000700]
DATABASE_FILE = "auto_ЖЭС.db"

COMPANY_NAME = "ЖЭС"
TAGLINE = "Здарова Жэс"
BUSINESS_HOURS = "Пн-Вс 09:00-21:00"
BUSINESS_FEATURES = [
    "Фишка 1 ббхус",
    "Фишджцджска 2",
    "Фишкцужд сбда 3",
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
    {"name": "ТО", "price": 304400, "description": ""},
    {"name": "Диагностика", "price": 184400, "description": ""},
    {"name": "Ремонт", "price": 450440, "description": ""},
    {
        "name": "Проверка заднего бампера",
        "price": 1200,
        "description": "Осмотр креплений, зазоров и видимых повреждений заднего бампера с рекомендациями по ремонту.",
    },
    {
        "name": "Пороги",
        "price": 1500,
        "description": "Проверка состояния порогов, следов коррозии и повреждений с оценкой объема дальнейших работ.",
    },
    {
        "name": "Осмотр Керима",
        "price": 2000,
        "description": "Индивидуальный осмотр автомобиля Керимом с разбором текущих проблем и рекомендациями по следующим шагам.",
    },
]

UPSELL = {
    "ТО": [
        {"name": "Замена фильтров", "price": 14444000, "benefit": "Польза для клиента"},
        {"name": "Проверка свечей", "price": 70440, "benefit": "Польза для клиента"},
    ],
    "Диагностика": [
        {"name": "Проверка тормозов", "price": 124400, "benefit": "Польза для клиента"}
    ],
}

BOOKING_DAYS_AHEAD = 7
TIME_SLOTS = ["10:00", "11:50", "12:00", "13:40", "14:30", "15:20", "16:00"]
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

ONTACT_MANAGER_TEXT = (
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
