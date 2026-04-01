# Default client profile for the bot.
# Copy this file to a new file (for example, alfa_service.py) and change values.

TOKEN = "8610850100:AAG74HVtAKWbKvajSwIxWZhJrDGjZw7_Nq0"
MANAGERS = [6271000700]
DATABASE_FILE = "auto.db"

COMPANY_NAME = "Автосервис"
TAGLINE = "Быстрый и честный сервис без лишних работ"
BUSINESS_HOURS = "Пн-Сб 09:00-21:00"
BUSINESS_FEATURES = [
    "Гарантия на работы",
    "Фото-отчет по ремонту",
    "Напоминания о записи",
]

WELCOME_TEXT = (
    "🚗 Добро пожаловать в {company_name}!\n\n"
    "Поможем подобрать удобную запись и сразу покажем стоимость услуг."
)
RETURNING_WELCOME_TEXT = "👋 {name}, рады вас снова видеть! Выберите, что хотите сделать дальше."
BOOKING_INTRO_TEXT = "Выберите основную услугу для записи:"
CATALOG_TITLE = "📘 Каталог услуг"
NO_UPSELL_TEXT = "Для этой услуги дополнительных работ сейчас нет."

SERVICES = [
    {
        "name": "ТО",
        "price": 3500,
        "description": "Плановое техническое обслуживание: базовая проверка и расходники.",
    },
    {
        "name": "Диагностика",
        "price": 2000,
        "description": "Компьютерная и ручная диагностика основных узлов автомобиля.",
    },
    {
        "name": "Ремонт",
        "price": 5000,
        "description": "Средняя стоимость слесарного ремонта без учета редких запчастей.",
    },
]

# Supports two formats:
# 1) list of dicts: {"name": ..., "price": ..., "benefit": ...}
# 2) list of strings: ["Проверка тормозов"]
UPSELL = {
    "ТО": [
        {
            "name": "Замена фильтров",
            "price": 1200,
            "benefit": "Помогает избежать лишней нагрузки на двигатель и систему вентиляции в ближайшие месяцы.",
        },
        {
            "name": "Проверка свечей",
            "price": 900,
            "benefit": "Позволяет заранее заметить износ и снизить риск проблем с запуском.",
        },
    ],
    "Диагностика": [
        {
            "name": "Проверка тормозов",
            "price": 1500,
            "benefit": "Позволяет заранее выявить износ колодок и дисков и избежать более дорогого ремонта позже.",
        }
    ],
    "Ремонт": [
        {
            "name": "Проверка фильтров",
            "price": 800,
            "benefit": "Своевременная проверка фильтров помогает избежать дополнительных работ и лишних расходов в будущем.",
        }
    ],
}

BOOKING_DAYS_AHEAD = 5
TIME_SLOTS = [
    "10:00",
    "11:00",
    "12:00",
    "13:00",
    "14:00",
    "15:00",
    "16:00",
    "17:00",
    "18:00",
    "19:00",
    "20:00",
]
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
    "Напишите менеджеру: {manager_link}\n"
    "ID менеджера: {manager_id}\n\n"
    "Если хотите, можете также описать вопрос здесь в чате, и мы передадим его менеджеру."
)

MANAGER_CONTACT_REQUEST_TEXT = (
    "📞 Клиент запросил связь с менеджером\n"
    "Клиент: {client_link}\n"
    "ID: {client_id}\n"
    "Username: {username}"
)
