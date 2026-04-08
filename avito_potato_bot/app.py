import json
import random
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "avito_potato.db"
CONFIG_PATH = BASE_DIR / "config.json"


class IncomingMessage(BaseModel):
    chat_id: str
    client_id: str
    client_name: str = ""
    text: str


class BotConfig:
    def __init__(self, data: dict):
        self.telegram_bot_token = str(data.get("telegram_bot_token", "")).strip()
        self.telegram_manager_chat_id = str(data.get("telegram_manager_chat_id", "")).strip()
        self.default_price_per_bag = int(data.get("default_price_per_bag", 1200))
        self.default_bag_weight_kg = int(data.get("default_bag_weight_kg", 25))
        self.delivery_windows = data.get("delivery_windows", ["днем", "вечером после обеда"])
        self.faq_answers = data.get("faq_answers", {})


def load_config() -> BotConfig:
    if not CONFIG_PATH.exists():
        raise RuntimeError("config.json not found. Copy config.example.json to config.json and fill credentials.")
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return BotConfig(json.load(f))


def normalize(text: str) -> str:
    text = text.lower().replace("ё", "е")
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


def contains_any(text: str, keywords) -> bool:
    n = normalize(text)
    return any(normalize(k) in n for k in keywords)


def classify_intent(text: str) -> Optional[str]:
    if contains_any(text, ["цена", "стоим", "сколько стоит", "почем"]):
        return "price"
    if contains_any(text, ["сколько кг", "килограмм", "в мешке", "вес мешка"]):
        return "weight"
    if contains_any(text, ["доставка", "когда привезете", "сегодня", "завтра", "когда можно"]):
        return "delivery"
    if contains_any(text, ["заказать", "оформить", "беру", "хочу купить", "куплю", "нужно"]):
        return "order"
    return None


def choose_answer(config: BotConfig, intent: str) -> str:
    defaults = {
        "price": [
            "Картошка сейчас {price} руб за мешок.",
            "Актуальная цена: {price} руб за мешок.",
        ],
        "weight": [
            "Обычно в одном мешке {weight} кг.",
            "Стандартный мешок: {weight} кг.",
        ],
        "delivery": [
            "Доставка есть: обычно днем или вечером после обеда.",
            "Можем доставить днем или вечером после обеда.",
        ],
    }
    variants = config.faq_answers.get(intent) or defaults[intent]
    return random.choice(variants).format(
        price=config.default_price_per_bag,
        weight=config.default_bag_weight_kg,
    )


def open_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


CONN = open_db()
CONFIG = load_config()
APP = FastAPI(title="Avito Potato Bot")


def setup_db() -> None:
    cur = CONN.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            chat_id TEXT PRIMARY KEY,
            client_id TEXT,
            client_name TEXT,
            state TEXT,
            quantity TEXT,
            delivery_day TEXT,
            delivery_window TEXT,
            address TEXT,
            entrance TEXT,
            phone TEXT,
            comment TEXT,
            updated_at TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            client_id TEXT,
            client_name TEXT,
            quantity TEXT,
            delivery_day TEXT,
            delivery_window TEXT,
            address TEXT,
            entrance TEXT,
            phone TEXT,
            comment TEXT,
            created_at TEXT
        )
        """
    )
    CONN.commit()


setup_db()


def get_session(chat_id: str) -> Optional[sqlite3.Row]:
    cur = CONN.cursor()
    cur.execute("SELECT * FROM sessions WHERE chat_id=?", (chat_id,))
    return cur.fetchone()


def upsert_session(chat_id: str, client_id: str, client_name: str, **fields) -> None:
    row = get_session(chat_id)
    now = datetime.utcnow().isoformat()
    if row is None:
        payload = {
            "chat_id": chat_id,
            "client_id": client_id,
            "client_name": client_name,
            "state": fields.get("state", ""),
            "quantity": fields.get("quantity", ""),
            "delivery_day": fields.get("delivery_day", ""),
            "delivery_window": fields.get("delivery_window", ""),
            "address": fields.get("address", ""),
            "entrance": fields.get("entrance", ""),
            "phone": fields.get("phone", ""),
            "comment": fields.get("comment", ""),
            "updated_at": now,
        }
        CONN.execute(
            """
            INSERT INTO sessions (
                chat_id, client_id, client_name, state,
                quantity, delivery_day, delivery_window,
                address, entrance, phone, comment, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(
                payload[k]
                for k in [
                    "chat_id",
                    "client_id",
                    "client_name",
                    "state",
                    "quantity",
                    "delivery_day",
                    "delivery_window",
                    "address",
                    "entrance",
                    "phone",
                    "comment",
                    "updated_at",
                ]
            ),
        )
    else:
        updates = []
        params = []
        for key, value in fields.items():
            updates.append(f"{key}=?")
            params.append(value)
        updates.extend(["client_id=?", "client_name=?", "updated_at=?"])
        params.extend([client_id, client_name, now, chat_id])
        CONN.execute(f"UPDATE sessions SET {', '.join(updates)} WHERE chat_id=?", tuple(params))
    CONN.commit()


def clear_session(chat_id: str) -> None:
    CONN.execute("DELETE FROM sessions WHERE chat_id=?", (chat_id,))
    CONN.commit()


def save_lead(row: sqlite3.Row) -> int:
    cur = CONN.cursor()
    cur.execute(
        """
        INSERT INTO leads (
            chat_id, client_id, client_name, quantity,
            delivery_day, delivery_window, address,
            entrance, phone, comment, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row["chat_id"],
            row["client_id"],
            row["client_name"],
            row["quantity"],
            row["delivery_day"],
            row["delivery_window"],
            row["address"],
            row["entrance"],
            row["phone"],
            row["comment"],
            datetime.utcnow().isoformat(),
        ),
    )
    CONN.commit()
    return int(cur.lastrowid)


def notify_telegram(lead_id: int, row: sqlite3.Row) -> None:
    if not CONFIG.telegram_bot_token or not CONFIG.telegram_manager_chat_id:
        return

    text = (
        f"Новая заявка #{lead_id}\n"
        f"Клиент: {row['client_name'] or 'не указано'}\n"
        f"client_id: {row['client_id']}\n"
        f"Количество: {row['quantity']}\n"
        f"День доставки: {row['delivery_day']}\n"
        f"Окно доставки: {row['delivery_window']}\n"
        f"Адрес: {row['address']}\n"
        f"Подъезд/этаж: {row['entrance']}\n"
        f"Телефон: {row['phone']}\n"
        f"Комментарий: {row['comment'] or '-'}"
    )

    payload = urlencode({"chat_id": CONFIG.telegram_manager_chat_id, "text": text}).encode("utf-8")
    req = Request(
        url=f"https://api.telegram.org/bot{CONFIG.telegram_bot_token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urlopen(req, timeout=10):
            pass
    except Exception:
        # Do not break message pipeline if telegram is temporarily unavailable.
        pass


def flow_reply(msg: IncomingMessage) -> Optional[str]:
    row = get_session(msg.chat_id)
    if row is None or not row["state"]:
        return None

    text = msg.text.strip()
    state = row["state"]

    if state == "ask_quantity":
        upsert_session(msg.chat_id, msg.client_id, msg.client_name, quantity=text, state="ask_delivery_day")
        return "Когда привезти: сегодня, завтра или в другой день?"

    if state == "ask_delivery_day":
        upsert_session(msg.chat_id, msg.client_id, msg.client_name, delivery_day=text, state="ask_delivery_window")
        return "По времени удобнее днем или вечером после обеда?"

    if state == "ask_delivery_window":
        upsert_session(msg.chat_id, msg.client_id, msg.client_name, delivery_window=text, state="ask_address")
        return "Напишите адрес доставки."

    if state == "ask_address":
        upsert_session(msg.chat_id, msg.client_id, msg.client_name, address=text, state="ask_entrance")
        return "Укажите подъезд/этаж (если нет, напишите 'нет')."

    if state == "ask_entrance":
        upsert_session(msg.chat_id, msg.client_id, msg.client_name, entrance=text, state="ask_phone")
        return "Оставьте номер телефона для подтверждения заказа."

    if state == "ask_phone":
        upsert_session(msg.chat_id, msg.client_id, msg.client_name, phone=text, state="ask_comment")
        return "Если есть комментарий, напишите. Если нет, ответьте 'нет'."

    if state == "ask_comment":
        comment = "" if normalize(text) in {"нет", "не", "-"} else text
        upsert_session(msg.chat_id, msg.client_id, msg.client_name, comment=comment)
        final_row = get_session(msg.chat_id)
        lead_id = save_lead(final_row)
        notify_telegram(lead_id, final_row)
        clear_session(msg.chat_id)
        return "Принял заявку. Сейчас передам менеджеру, он свяжется с вами для подтверждения."

    return None


def build_reply(msg: IncomingMessage) -> str:
    reply = flow_reply(msg)
    if reply:
        return reply

    intent = classify_intent(msg.text)
    if intent == "order":
        upsert_session(msg.chat_id, msg.client_id, msg.client_name, state="ask_quantity")
        return "Отлично, оформим заказ. Сколько мешков нужно?"

    if intent in {"price", "weight", "delivery"}:
        return choose_answer(CONFIG, intent) + " Если хотите, могу сразу оформить заказ."

    return (
        "Подскажу быстро: могу ответить по цене, весу мешка и доставке, "
        "или сразу оформить заказ в несколько шагов."
    )


@APP.get("/health")
def health() -> dict:
    return {"ok": True, "time": datetime.utcnow().isoformat()}


@APP.post("/webhook/incoming")
def incoming(msg: IncomingMessage) -> dict:
    text = msg.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="empty text")
    return {"reply_text": build_reply(msg)}
