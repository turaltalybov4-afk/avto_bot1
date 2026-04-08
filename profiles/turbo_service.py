TOKEN = "8745064857:AAGkoPZ1Xzas2ZYvUvBxCgWYrYxoe7D9qek"
MANAGERS = [6271000700]
DATABASE_FILE = "auto_turbo_service.db"  

COMPANY_NAME = "Turbo Service"
TAGLINE = "Честная диагностика и понятный ремонт без лишних работ"
BUSINESS_HOURS = "Пн-Вс 10:00-20:00"
BUSINESS_FEATURES = [
    "Фото и видео-отчет по работам",
    "Подбор удобного времени в один клик",
    "Напоминания клиенту за 24 и 2 часа",
]

WELCOME_TEXT = (
    "🚗 Добро пожаловать в {company_name}!\n\n"
    "Поможем быстро записаться, покажем стоимость услуг и подберем удобное время."
)
RETURNING_WELCOME_TEXT = "👋 {name}, рады вас снова видеть в Turbo Service! Выберите, что хотите сделать дальше."
BOOKING_INTRO_TEXT = "Выберите услугу, на которую хотите записаться:"
CATALOG_TITLE = "📘 Каталог услуг Turbo Service"
NO_UPSELL_TEXT = "Для этой услуги сейчас нет дополнительных предложений."

SERVICES = [
    {
        "name": "Диагностика двигателя",
        "price": 2500,
        "description": "Комплексная проверка двигателя и электронных систем с расшифровкой ошибок.",
    },
    {
        "name": "Замена масла",
        "price": 2200,
        "description": "Замена моторного масла и базовая проверка состояния подкапотного пространства.",
    },
    {
        "name": "Тормозная система",
        "price": 3200,
        "description": "Осмотр и обслуживание тормозной системы с оценкой износа расходников.",
    },
]

UPSELL = {
    "Диагностика двигателя": [
        {
            "name": "Проверка катушек зажигания",
            "price": 1200,
            "benefit": "Помогает заранее найти причину троения и избежать более дорогого ремонта позже.",
        },
        {
            "name": "Проверка свечей",
            "price": 900,
            "benefit": "Позволяет увидеть износ и не довести проблему до плохого запуска двигателя.",
        },
    ],
    "Замена масла": [
        {
            "name": "Проверка фильтров",
            "price": 800,
            "benefit": "Своевременная проверка фильтров помогает избежать дополнительных расходов в будущем.",
        }
    ],
    "Тормозная система": [
        {
            "name": "Проверка тормозной жидкости",
            "price": 1000,
            "benefit": "Позволяет заранее увидеть ухудшение свойств жидкости и сохранить стабильное торможение.",
        }
    ],
}

BOOKING_DAYS_AHEAD = 5
TIMEZONE = "Asia/Krasnoyarsk"
TIME_SLOTS = ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"]
BOOKING_HOLD_MINUTES = 30
WEEKLY_REPORT_WEEKDAY = 0
WEEKLY_REPORT_HOUR = 9

MANAGER_NEW_BOOKING_TITLE = "📥 Новая запись Turbo Service"
MANAGER_HISTORY_TITLE = "📊 История клиента"
MANAGER_REVENUE_TITLE = "💰 Доход по клиенту"
MANAGER_WEEKLY_REPORT_TITLE = "📈 Итоги недели Turbo Service"

REMINDER_24H_TEXT = "👋 Напоминаем о записи завтра в {time}. Будем рады видеть вас в Turbo Service!"
REMINDER_2H_TEXT = "⏰ Напоминаем: запись сегодня в {time}. Подтвердите, пожалуйста, визит."
ABANDONED_BOOKING_TEXT = "👋 {name}, вы не закончили запись в Turbo Service. Если хотите, поможем подобрать удобное время."

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
    "📞 Связь с менеджером Turbo Service\n\n"
    "Напишите менеджеру: {manager_link}\n"
    "ID менеджера: {manager_id}\n\n"
    "Или просто отправьте сообщение сюда, и мы сразу передадим его менеджеру."
)

MANAGER_CONTACT_REQUEST_TEXT = (
    "📞 Клиент попросил связаться с менеджером\n"
    "Клиент: {client_link}\n"
    "ID: {client_id}\n"
    "Username: {username}"
)

REVIEW_PUBLIC_LINKS = [
    "https://yandex.ru/maps/",
    "https://2gis.ru/",
]

CONTACT_MANAGER_PROMPT_TEXT = "✍️ Напишите ваш вопрос в чат, и мы сразу отправим его менеджеру."

MANAGER_CLIENT_MESSAGE_TEXT = (
    "💬 Новое сообщение от клиента Turbo Service\n"
    "Клиент: {client_link}\n"
    "ID: {client_id}\n"
    "Username: {username}\n\n"
    "Сообщение:\n{message}"
)
