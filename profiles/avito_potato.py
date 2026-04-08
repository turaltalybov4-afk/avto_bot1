# Profile example for Avito produce sales.
# Enable with: AUTOBOT_PROFILE=avito_potato

TOKEN = "PUT_BOT_TOKEN_HERE"
MANAGERS = [111111111]
DATABASE_FILE = "auto_avito_potato.db"

COMPANY_NAME = "Картофель с базы"
TAGLINE = "Свежий картофель оптом и в розницу"
BUSINESS_HOURS = "Ежедневно 08:00-22:00"
BUSINESS_FEATURES = [
    "Быстрый ответ в чате",
    "Доставка в день заказа",
    "Скидка от объема",
]

WELCOME_TEXT = (
    "Добро пожаловать в {company_name}!\n\n"
    "Отвечу по цене, фасовке и помогу быстро оформить заявку."
)
RETURNING_WELCOME_TEXT = "Рады снова видеть, {name}. Что подскажу?"
BOOKING_INTRO_TEXT = "Выберите товар:"
CATALOG_TITLE = "Каталог товаров"
NO_UPSELL_TEXT = "Сейчас дополнительных позиций нет."

SERVICES = [
    {
        "name": "Картошка",
        "price": 1200,
        "description": "Цена за мешок. Возможны скидки от объема.",
        "aliases": ["картофель", "картошка мешок"],
    },
    {
        "name": "Лук",
        "price": 900,
        "description": "Свежий лук в мешках.",
        "aliases": ["лук мешок"],
    },
]

UPSELL = {
    "Картошка": [
        {
            "name": "Подъем на этаж",
            "price": 300,
            "benefit": "Не нужно поднимать мешки самостоятельно.",
        },
        {
            "name": "Разгрузка во двор",
            "price": 200,
            "benefit": "Быстрая разгрузка на месте.",
        },
    ],
    "Лук": [
        {
            "name": "Подъем на этаж",
            "price": 300,
            "benefit": "Не нужно поднимать мешки самостоятельно.",
        }
    ],
}

FAQ_ITEMS = [
    {
        "triggers": ["сколько килограмм", "сколько кг", "в мешке", "вес мешка"],
        "answers": [
            "Стандартно 25 кг в мешке. Если нужен другой вес, тоже подберем.",
            "Обычно мешок 25 кг. Можем собрать и другой объем под ваш заказ.",
        ],
    },
    {
        "triggers": ["доставка", "привезете", "когда привезете"],
        "answers": [
            "Доставляем сегодня или завтра, в зависимости от вашего района и времени.",
            "Да, доставка есть. Напишите район и удобный интервал времени.",
        ],
    },
]

BOOKING_DAYS_AHEAD = 5
TIME_SLOTS = ["10:00", "12:00", "14:00", "16:00", "18:00", "20:00"]
BOOKING_HOLD_MINUTES = 30
WEEKLY_REPORT_WEEKDAY = 0
WEEKLY_REPORT_HOUR = 9

MANAGER_NEW_BOOKING_TITLE = "Новая запись"
MANAGER_HISTORY_TITLE = "История клиента"
MANAGER_REVENUE_TITLE = "Финансы клиента"
MANAGER_WEEKLY_REPORT_TITLE = "Итоги за неделю"
MANAGER_LEAD_TITLE = "Новая заявка из Avito-чата"

REMINDER_24H_TEXT = "Напоминаем о заказе завтра в {time}."
REMINDER_2H_TEXT = "Напоминаем: заказ сегодня в {time}."
ABANDONED_BOOKING_TEXT = "Вы не закончили заявку. Помочь продолжить?"

BUTTON_BOOK = "Оформить заявку"
BUTTON_CATALOG = "Каталог"
BUTTON_CONTACT_MANAGER = "Связь с менеджером"
BUTTON_MAIN_MENU = "Главное меню"
BUTTON_BACK_TO_BOOKING = "Вернуться"
BUTTON_CONFIRM = "Подтвердить"
BUTTON_COMING = "Подтверждаю"
BUTTON_CANCEL = "Отменить"
BUTTON_RESCHEDULE = "Перенести"

CONTACT_MANAGER_TEXT = (
    "Связь с менеджером\n\n"
    "Напишите менеджеру: {manager_link}\n"
    "ID менеджера: {manager_id}"
)

MANAGER_CONTACT_REQUEST_TEXT = (
    "Клиент запросил связь с менеджером\n"
    "Клиент: {client_link}\n"
    "ID: {client_id}\n"
    "Username: {username}"
)

ORDER_START_KEYWORDS = [
    "заказать",
    "оформить",
    "нужна доставка",
    "купить",
    "оставить заявку",
]
LEAD_PROMPT_QUANTITY = "Сколько нужно? Например: 5 мешков по 25 кг."
LEAD_PROMPT_DATE = "Когда удобно получить: сегодня, завтра или другая дата?"
LEAD_PROMPT_CONTACT = "Оставьте телефон для подтверждения заказа."
LEAD_PROMPT_COMMENT = "Напишите адрес/комментарий. Если без комментария, ответьте 'нет'."
LEAD_SUCCESS_TEXT = "Принял заявку. Менеджер скоро свяжется для подтверждения."
LEAD_SKIP_WORDS = ["нет", "не", "-"]
