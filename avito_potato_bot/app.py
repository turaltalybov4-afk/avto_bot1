import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple
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
    client_name: Optional[str] = ""
    text: str


class BotConfig:
    def __init__(self, data: dict):
        self.avito_api_base = data.get("avito_api_base", "https://api.avito.ru")
        self.avito_access_token = data.get("avito_access_token", "")
        self.telegram_bot_token = data.get("telegram_bot_token", "")
        self.telegram_manager_chat_id = str(data.get("telegram_manager_chat_id", "")).strip()
        self.default_price_per_bag = int(data.get("default_price_per_bag", 1200))
        self.default_bag_weight_kg = int(data.get("default_bag_weight_kg", 25))
        self.delivery_windows = data.get("delivery_windows", ["днем", "вечером после обеда"])


def load_config() -> BotConfig:
    if not CONFIG_PATH.exists():
        raise RuntimeError("config.json not found. Copy config.example.json to config.json and fill credentials.")
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return BotConfig(json.load(f))


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


CONN = db()
CONFIG = load_config()
APP = FastAPI(title="Avito Potato Assistant")


def setup_db() -> None:
    cur = CONN.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            chat_id TEXT PRIMARY KEY,
            client_id TEXT,
            client_name TEXT,
            state TEXT,
            lead_quantity TEXT,
            lead_delivery_day TEXT,
            lead_delivery_window TEXT,
            lead_address TEXT,
            lead_entrance TEXT,
            lead_phone TEXT,
            lead_comment TEXT,
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


def normalize(text: str) -> str:
    text = text.lower().replace("ё", "е")
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


def contains_any(text: str, keywords) -> bool:
    n = normalize(text)
    return any(normalize(k) in n for k in keywords)


def classify_question(text: str) -> Optional[str]:
    n = normalize(text)

    if contains_any(n, ["цена", "стоит", "сколько", "почем"]):
        return "price"
    if contains_any(n, ["в мешке", "сколько кг", "вес мешка", "килограмм"]):
        return "weight"
    if contains_any(n, ["доставка", "когда привезете", "срок", "сегодня", "завтра"]):
        return "delivery"
    if contains_any(n, ["заказать", "оформить", "беру", "хочу купить", "нужно"]):
        return "order"
    return None


def faq_answer(intent: str) -> str:
    if intent == "price":
        return f"Сейчас цена {CONFIG.default_price_per_bag} руб за мешок. Если берете объем, сделаем скидку."
    if intent == "weight":
        return f"В одном мешке обычно {CONFIG.default_bag_weight_kg} кг."
    if intent == "delivery":
        return (
            "Доставка возможна сегодня или завтра. Обычно привозим "
            f"{CONFIG.delivery_windows[0]} или {CONFIG.delivery_windows[1]}."
        )
    return "Подскажу все детали и помогу оформить заказ за пару сообщений."


def get_session(chat_id: str) -> Optional[sqlite3.Row]:
    cur = CONN.cursor()
    cur.execute("SELECT * FROM sessions WHERE chat_id=?", (chat_id,))
    return cur.fetchone()


def upsert_session(chat_id: str, client_id: str, client_name: str, **fields) -> None:
    row = get_session(chat_id)
    now = datetime.utcnow().isoformat()
    if row is None:
        values = {
            "chat_id": chat_id,
            "client_id": client_id,
            "client_name": client_name or "",
            "state": fields.get("state", ""),
            "lead_quantity": fields.get("lead_quantity", ""),
            "lead_delivery_day": fields.get("lead_delivery_day", ""),
            "lead_delivery_window": fields.get("lead_delivery_window", ""),
            "lead_address": fields.get("lead_address", ""),
            "lead_entrance": fields.get("lead_entrance", ""),
            "lead_phone": fields.get("lead_phone", ""),
            "lead_comment": fields.get("lead_comment", ""),
            "updated_at": now,
        }
        CONN.execute(
            """
            INSERT INTO sessions (
                chat_id, client_id, client_name, state,
                lead_quantity, lead_delivery_day, lead_delivery_window,
                lead_address, lead_entrance, lead_phone, lead_comment,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(values[k] for k in [
                "chat_id", "client_id", "client_name", "state",
                "lead_quantity", "lead_delivery_day", "lead_delivery_window",
                "lead_address", "lead_entrance", "lead_phone", "lead_comment",
                "updated_at",
            ]),
        )
    else:
        updates = []
        params = []
        for key, value in fields.items():
            updates.append(f"{key}=?")
            params.append(value)
        updates.append("client_id=?")
        updates.append("client_name=?")
        updates.append("updated_at=?")
        params.extend([client_id, client_name or "", now, chat_id])
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
            row["lead_quantity"],
            row["lead_delivery_day"],
            row["lead_delivery_window"],
            row["lead_address"],
            row["lead_entrance"],
            row["lead_phone"],
            row["lead_comment"],
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
        f"Client ID: {row['client_id']}\n"
        f"Количество: {row['lead_quantity']}\n"
        f"День: {row['lead_delivery_day']}\n"
        f"Время: {row['lead_delivery_window']}\n"
        f"Адрес: {row['lead_address']}\n"
        f"Подъезд: {row['lead_entrance']}\n"
        f"Телефон: {row['lead_phone']}\n"
        f"Комментарий: {row['lead_comment'] or '-'}"
    )

    payload = urlencode({
        "chat_id": CONFIG.telegram_manager_chat_id,
        "text": text,
    }).encode("utf-8")

    req = Request(
        url=f"https://api.telegram.org/bot{CONFIG.telegram_bot_token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urlopen(req, timeout=8):
            pass
    except Exception:
        pass


def next_flow_reply(chat_id: str, client_id: str, client_name: str, text: str) -> Optional[str]:
    row = get_session(chat_id)
    if row is None or not row["state"]:
        return None

    state = row["state"]
    clean = text.strip()

    if state == "ask_quantity":
        upsert_session(chat_id, client_id, client_name, lead_quantity=clean, state="ask_delivery_day")
        return "Когда привезти: сегодня, завтра или другой день?"

    if state == "ask_delivery_day":
        upsert_session(chat_id, client_id, client_name, lead_delivery_day=clean, state="ask_delivery_window")
        return "Удобнее днем или вечером после обеда?"

    if state == "ask_delivery_window":
        upsert_session(chat_id, client_id, client_name, lead_delivery_window=clean, state="ask_address")
        return "Напишите адрес доставки."

    if state == "ask_address":
        upsert_session(chat_id, client_id, client_name, lead_address=clean, state="ask_entrance")
        return "Укажите подъезд/этаж (если нет, напишите 'нет')."

    if state == "ask_entrance":
        upsert_session(chat_id, client_id, client_name, lead_entrance=clean, state="ask_phone")
        return "Оставьте номер телефона для подтверждения."

    if state == "ask_phone":
        upsert_session(chat_id, client_id, client_name, lead_phone=clean, state="ask_comment")
        return "Есть комментарий к заказу? Если нет, напишите 'нет'."

    if state == "ask_comment":
        comment = "" if normalize(clean) in {"нет", "не", "-"} else clean
        upsert_session(chat_id, client_id, client_name, lead_comment=comment)
        final = get_session(chat_id)
        lead_id = save_lead(final)
        notify_telegram(lead_id, final)
        clear_session(chat_id)
        return "Отлично, заявку принял. Сейчас передам менеджеру, он свяжется для подтверждения."

    return None


def maybe_start_order(chat_id: str, client_id: str, client_name: str, text: str) -> Tuple[bool, str]:
    intent = classify_question(text)
    if intent == "order":
        upsert_session(chat_id, client_id, client_name, state="ask_quantity")
        return True, "Супер, оформим заказ. Сколько мешков нужно?"
    return False, ""


def build_reply(chat_id: str, client_id: str, client_name: str, text: str) -> str:
    flow_reply = next_flow_reply(chat_id, client_id, client_name, text)
    if flow_reply:
        return flow_reply

    started, reply = maybe_start_order(chat_id, client_id, client_name, text)
    if started:
        return reply

    intent = classify_question(text)
    if intent:
        return faq_answer(intent) + " Если хотите, могу сразу оформить заказ."

    return (
        "Подскажу быстро. Могу ответить по цене, весу мешка и доставке, "
        "или сразу оформить заказ в 6 коротких шагов."
    )


@APP.get("/health")
def health():
    return {"ok": True, "time": datetime.utcnow().isoformat()}


@APP.post("/webhook/incoming")
def incoming(msg: IncomingMessage):
    text = (msg.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="empty text")

    reply = build_reply(msg.chat_id, msg.client_id, msg.client_name or "", text)
    return {"reply_text": reply}
