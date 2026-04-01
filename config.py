import importlib
import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).with_name(".env"), override=False)


def _load_profile_module():
    profile_name = os.getenv("AUTOBOT_PROFILE", "default").strip() or "default"
    module_name = f"profiles.{profile_name}"
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        if profile_name != "default":
            module = importlib.import_module("profiles.default")
            profile_name = "default"
        else:
            raise
    return profile_name, module


def _pick(module, key, default):
    return getattr(module, key, default)


def _env_str(name, default=""):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip()


def _env_int(name, default):
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return int(value)


def _env_list_of_ints(name, default):
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default
    return [int(item.strip()) for item in raw_value.split(",") if item.strip()]


def _normalize_services(raw_services):
    normalized = []
    for service in raw_services:
        if not isinstance(service, dict):
            continue
        normalized.append(
            {
                "name": str(service.get("name", "")).strip(),
                "price": int(service.get("price", 0)),
                "description": str(service.get("description", "")).strip(),
            }
        )
    return [s for s in normalized if s["name"]]


def _normalize_upsell(raw_upsell):
    normalized = {}

    for service_name, items in raw_upsell.items():
        clean_items = []
        for item in items:
            if isinstance(item, str):
                clean_items.append(
                    {
                        "name": item.strip(),
                        "price": 0,
                        "benefit": "",
                    }
                )
            elif isinstance(item, dict):
                clean_items.append(
                    {
                        "name": str(item.get("name", "")).strip(),
                        "price": int(item.get("price", 0)),
                        "benefit": str(item.get("benefit", "")).strip(),
                    }
                )
        normalized[str(service_name)] = [i for i in clean_items if i["name"]]

    return normalized


PROFILE_NAME, _profile = _load_profile_module()
PROFILE_SLUG = PROFILE_NAME

DEFAULT_DATABASE_FILE = "auto.db" if PROFILE_NAME == "default" else f"auto_{PROFILE_NAME}.db"

# For multi-profile setups, profile values must have priority.
# Environment variables are only used as fallback if profile fields are missing.
TOKEN = _pick(_profile, "TOKEN", "") or _env_str("BOT_TOKEN", "")
MANAGERS = _pick(_profile, "MANAGERS", []) or _env_list_of_ints("AUTOBOT_MANAGERS", [])
DATABASE_FILE = _pick(_profile, "DATABASE_FILE", "") or _env_str("AUTOBOT_DATABASE_FILE", DEFAULT_DATABASE_FILE)

COMPANY_NAME = _pick(_profile, "COMPANY_NAME", "Автосервис")
TAGLINE = _pick(_profile, "TAGLINE", "")
BUSINESS_HOURS = _pick(_profile, "BUSINESS_HOURS", "")
BUSINESS_FEATURES = _pick(_profile, "BUSINESS_FEATURES", [])

WELCOME_TEXT = _pick(
    _profile,
    "WELCOME_TEXT",
    "🚗 Добро пожаловать в {company_name}!\n\nПоможем подобрать удобную запись и сразу покажем стоимость услуг.",
)
RETURNING_WELCOME_TEXT = _pick(
    _profile,
    "RETURNING_WELCOME_TEXT",
    "👋 {name}, рады вас снова видеть! Выберите, что хотите сделать дальше.",
)
BOOKING_INTRO_TEXT = _pick(_profile, "BOOKING_INTRO_TEXT", "Выберите основную услугу для записи:")
CATALOG_TITLE = _pick(_profile, "CATALOG_TITLE", "📘 Каталог услуг")
NO_UPSELL_TEXT = _pick(_profile, "NO_UPSELL_TEXT", "Для этой услуги дополнительных работ сейчас нет.")

SERVICES = _normalize_services(_pick(_profile, "SERVICES", []))
UPSELL = _normalize_upsell(_pick(_profile, "UPSELL", {}))

BOOKING_DAYS_AHEAD = _env_int("AUTOBOT_BOOKING_DAYS_AHEAD", int(_pick(_profile, "BOOKING_DAYS_AHEAD", 5)))
TIME_SLOTS = [str(x) for x in _pick(_profile, "TIME_SLOTS", ["10:00", "12:00", "14:00", "16:00"])]
BOOKING_HOLD_MINUTES = _env_int("AUTOBOT_BOOKING_HOLD_MINUTES", int(_pick(_profile, "BOOKING_HOLD_MINUTES", 30)))
WEEKLY_REPORT_WEEKDAY = _env_int("AUTOBOT_WEEKLY_REPORT_WEEKDAY", int(_pick(_profile, "WEEKLY_REPORT_WEEKDAY", 0)))
WEEKLY_REPORT_HOUR = _env_int("AUTOBOT_WEEKLY_REPORT_HOUR", int(_pick(_profile, "WEEKLY_REPORT_HOUR", 9)))

MANAGER_NEW_BOOKING_TITLE = _pick(_profile, "MANAGER_NEW_BOOKING_TITLE", "📥 Новая запись")
MANAGER_HISTORY_TITLE = _pick(_profile, "MANAGER_HISTORY_TITLE", "📊 История клиента")
MANAGER_REVENUE_TITLE = _pick(_profile, "MANAGER_REVENUE_TITLE", "💰 Финансы клиента")
MANAGER_WEEKLY_REPORT_TITLE = _pick(_profile, "MANAGER_WEEKLY_REPORT_TITLE", "📈 Итоги за последнюю неделю")

REMINDER_24H_TEXT = _pick(
    _profile,
    "REMINDER_24H_TEXT",
    "👋 Напоминаем о записи завтра в {time}. Будем рады вас видеть!",
)
REMINDER_2H_TEXT = _pick(
    _profile,
    "REMINDER_2H_TEXT",
    "⏰ Напоминаем: запись сегодня в {time}. Подтвердите, пожалуйста, визит.",
)
ABANDONED_BOOKING_TEXT = _pick(
    _profile,
    "ABANDONED_BOOKING_TEXT",
    "👋 {name}, вы не закончили запись. Можем помочь подобрать удобное время.",
)

BUTTON_BOOK = _pick(_profile, "BUTTON_BOOK", "🛠 Записаться")
BUTTON_CATALOG = _pick(_profile, "BUTTON_CATALOG", "📘 Каталог услуг")
BUTTON_CONTACT_MANAGER = _pick(_profile, "BUTTON_CONTACT_MANAGER", "📞 Связаться с менеджером")
BUTTON_MAIN_MENU = _pick(_profile, "BUTTON_MAIN_MENU", "🏠 Главное меню")
BUTTON_BACK_TO_BOOKING = _pick(_profile, "BUTTON_BACK_TO_BOOKING", "↩️ Вернуться к записи")
BUTTON_CONFIRM = _pick(_profile, "BUTTON_CONFIRM", "Подтвердить")
BUTTON_COMING = _pick(_profile, "BUTTON_COMING", "✅ Приду")
BUTTON_CANCEL = _pick(_profile, "BUTTON_CANCEL", "❌ Отменить")
BUTTON_RESCHEDULE = _pick(_profile, "BUTTON_RESCHEDULE", "🔁 Перенести")

CONTACT_MANAGER_TEXT = _pick(
    _profile,
    "CONTACT_MANAGER_TEXT",
    (
        "📞 Связь с менеджером\n\n"
        "Напишите менеджеру: {manager_link}\n"
        "ID менеджера: {manager_id}\n\n"
        "Если хотите, можете также описать вопрос здесь в чате, и мы передадим его менеджеру."
    ),
)

MANAGER_CONTACT_REQUEST_TEXT = _pick(
    _profile,
    "MANAGER_CONTACT_REQUEST_TEXT",
    (
        "📞 Клиент запросил связь с менеджером\n"
        "Клиент: {client_link}\n"
        "ID: {client_id}\n"
        "Username: {username}"
    ),
)

CONTACT_MANAGER_PROMPT_TEXT = _pick(
    _profile,
    "CONTACT_MANAGER_PROMPT_TEXT",
    "✍️ Напишите сообщение для менеджера в чат. Мы сразу его передадим.",
)

MANAGER_CLIENT_MESSAGE_TEXT = _pick(
    _profile,
    "MANAGER_CLIENT_MESSAGE_TEXT",
    (
        "💬 Новое сообщение от клиента\n"
        "Клиент: {client_link}\n"
        "ID: {client_id}\n"
        "Username: {username}\n\n"
        "Сообщение:\n{message}"
    ),
)
