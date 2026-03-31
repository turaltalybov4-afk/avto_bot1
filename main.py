import asyncio
import datetime
from html import escape
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import config
import database


user_state = {}
user_data_temp = {}
maintenance_mode = False
BUSY_STATUSES = ("booked", "confirmed_by_client", "pending", "approved")
ACTIVE_BOOKING_STATUSES = ("booked", "confirmed_by_client", "pending", "approved")
INACTIVE_BOOKING_STATUSES = ("cancelled", "rejected", "reschedule_requested")


def format_money(amount: int) -> str:
    return f"{int(amount):,}".replace(",", " ")


def get_service_by_name(service_name: str):
    for service in config.SERVICES:
        if service["name"] == service_name:
            return service
    return None


def get_upsells_for_service(service_name: str):
    return config.UPSELL.get(service_name, [])


def get_upsell_by_name(service_name: str, upsell_name: str):
    for upsell in get_upsells_for_service(service_name):
        if upsell["name"] == upsell_name:
            return upsell
    return None


def get_meta(key: str):
    database.cursor.execute("SELECT value FROM app_meta WHERE key=?", (key,))
    row = database.cursor.fetchone()
    return row[0] if row else None


def set_meta(key: str, value: str):
    database.cursor.execute(
        "INSERT OR REPLACE INTO app_meta (key, value) VALUES (?, ?)",
        (key, value),
    )
    database.conn.commit()


def booking_is_active(user_id: int) -> bool:
    return user_id in user_data_temp and user_data_temp[user_id].get("booking_started", False)


def reset_booking_state(user_id: int):
    user_state.pop(user_id, None)
    user_data_temp.pop(user_id, None)


def touch_booking(user_id: int, user=None):
    if user_id not in user_data_temp:
        return

    draft = user_data_temp[user_id]
    draft["last_activity"] = datetime.datetime.now().isoformat()
    draft["inactivity_reminder_sent"] = False

    if user is not None:
        draft["client_id"] = user.id
        draft["client_first_name"] = user.first_name or "Клиент"
        draft["client_username"] = user.username


def start_booking_draft(user):
    user_state.pop(user.id, None)
    user_data_temp[user.id] = {
        "booking_started": True,
        "client_id": user.id,
        "client_first_name": user.first_name or "Клиент",
        "client_username": user.username,
        "selected_upsells": [],
        "last_activity": datetime.datetime.now().isoformat(),
        "inactivity_reminder_sent": False,
    }


def build_main_menu_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(config.BUTTON_BOOK, callback_data="start_booking"),
                InlineKeyboardButton(config.BUTTON_CATALOG, callback_data="show_catalog"),
            ],
            [InlineKeyboardButton(config.BUTTON_CONTACT_MANAGER, callback_data="contact_manager")],
        ]
    )


def build_navigation_rows(include_restart: bool = True):
    rows = []
    if include_restart:
        rows.append([InlineKeyboardButton(config.BUTTON_BACK_TO_BOOKING, callback_data="start_booking")])
    rows.append(
        [
            InlineKeyboardButton(config.BUTTON_CATALOG, callback_data="show_catalog"),
            InlineKeyboardButton(config.BUTTON_MAIN_MENU, callback_data="main_menu"),
        ]
    )
    return rows


def build_prompt_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(build_navigation_rows())


def build_service_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                f"{service['name']} — {format_money(service['price'])}₽",
                callback_data=f"service_{service['name']}",
            )
        ]
        for service in config.SERVICES
    ]
    rows.extend(build_navigation_rows(include_restart=False))
    return InlineKeyboardMarkup(rows)


def chunk_buttons(buttons, per_row: int):
    return [buttons[i : i + per_row] for i in range(0, len(buttons), per_row)]


def format_date_ru(date_obj: datetime.date, include_year: bool = False) -> str:
    months = {
        1: "Января",
        2: "Февраля",
        3: "Марта",
        4: "Апреля",
        5: "Мая",
        6: "Июня",
        7: "Июля",
        8: "Августа",
        9: "Сентября",
        10: "Октября",
        11: "Ноября",
        12: "Декабря",
    }
    date_text = f"{date_obj.day} {months[date_obj.month]}"
    if include_year:
        date_text += f" {date_obj.year}"
    return date_text


def format_date_str_ru(date_str: str, include_year: bool = False) -> str:
    try:
        date_obj = datetime.date.fromisoformat(date_str)
    except (ValueError, TypeError):
        return str(date_str)
    return format_date_ru(date_obj, include_year=include_year)


def build_date_keyboard() -> InlineKeyboardMarkup:
    today = datetime.date.today()
    date_buttons = [
        InlineKeyboardButton(
            format_date_ru(today + datetime.timedelta(days=i)),
            callback_data=f"date_{i}",
        )
        for i in range(config.BOOKING_DAYS_AHEAD)
    ]
    rows = chunk_buttons(date_buttons, 2)
    rows.extend(build_navigation_rows())
    return InlineKeyboardMarkup(rows)


def get_busy_slots(date: str):
    database.cursor.execute(
        """
        SELECT time FROM bookings
        WHERE date=? AND status IN (?, ?, ?, ?)
        """,
        (date, *BUSY_STATUSES),
    )
    return {row[0] for row in database.cursor.fetchall()}


def is_time_available(date: str, time: str) -> bool:
    return time not in get_busy_slots(date)


def build_time_keyboard(date: str):
    busy_slots = get_busy_slots(date)
    free_slots = [slot for slot in config.TIME_SLOTS if slot not in busy_slots]
    time_buttons = [InlineKeyboardButton(slot, callback_data=f"time_{slot}") for slot in free_slots]
    rows = chunk_buttons(time_buttons, 3)
    rows.extend(build_navigation_rows())
    return InlineKeyboardMarkup(rows), free_slots


def build_catalog_text() -> str:
    lines = [config.CATALOG_TITLE, ""]

    for service in config.SERVICES:
        lines.append(f"• {service['name']} — {format_money(service['price'])}₽")
        lines.append(service["description"])
        lines.append("")

    return "\n".join(lines).strip()


def build_catalog_markup(user_id: int) -> InlineKeyboardMarkup:
    rows = []
    if booking_is_active(user_id):
        rows.append([InlineKeyboardButton(config.BUTTON_BACK_TO_BOOKING, callback_data="resume_booking")])
    else:
        rows.append([InlineKeyboardButton(config.BUTTON_BOOK, callback_data="start_booking")])
    rows.append([InlineKeyboardButton(config.BUTTON_MAIN_MENU, callback_data="main_menu")])
    return InlineKeyboardMarkup(rows)


def get_selected_upsells(user_id: int):
    return user_data_temp[user_id].get("selected_upsells", [])


def calculate_booking_totals(user_id: int):
    draft = user_data_temp[user_id]
    service = get_service_by_name(draft["service"])
    service_price = service["price"] if service else 0
    selected = get_selected_upsells(user_id)
    upsell_total = sum(item["price"] for item in selected)
    return service_price, upsell_total, service_price + upsell_total


def build_upsell_prompt(user_id: int):
    draft = user_data_temp[user_id]
    service = get_service_by_name(draft["service"])
    selected_names = {item["name"] for item in get_selected_upsells(user_id)}
    service_price, upsell_total, total_price = calculate_booking_totals(user_id)

    lines = [
        f"Основная услуга: {service['name']} — {format_money(service_price)}₽",
        "",
        "💡 Можно добавить к записи:",
    ]
    rows = []

    upsells = get_upsells_for_service(service["name"])
    if upsells:
        for upsell in upsells:
            marker = "✅" if upsell["name"] in selected_names else "◻️"
            lines.append(f"{marker} {upsell['name']} — {format_money(upsell['price'])}₽")
            lines.append(upsell["benefit"])
            rows.append(
                [
                    InlineKeyboardButton(
                        f"{marker} {upsell['name']} — {format_money(upsell['price'])}₽",
                        callback_data=f"upsell_{upsell['name']}",
                    )
                ]
            )
    else:
        lines.append(config.NO_UPSELL_TEXT)

    if selected_names:
        lines.append("")
        lines.append("Выбрано:")
        for item in get_selected_upsells(user_id):
            lines.append(f"• {item['name']} — {format_money(item['price'])}₽")

    lines.append("")
    lines.append(f"Доп. услуги: {format_money(upsell_total)}₽")
    lines.append(f"Итого по записи: {format_money(total_price)}₽")

    rows.append([InlineKeyboardButton(config.BUTTON_CONFIRM, callback_data="confirm")])
    rows.extend(build_navigation_rows())
    return "\n".join(lines), InlineKeyboardMarkup(rows)


def get_client_name_for_message(update: Update) -> str:
    if update.effective_user and update.effective_user.first_name:
        return update.effective_user.first_name
    return "Клиент"


def build_main_menu_text(name: Optional[str] = None) -> str:
    lines = []

    if name:
        lines.append(config.RETURNING_WELCOME_TEXT.format(name=name))
    else:
        lines.append(config.WELCOME_TEXT.format(company_name=config.COMPANY_NAME))

    if config.TAGLINE:
        lines.append("")
        lines.append(config.TAGLINE)

    if config.BUSINESS_HOURS:
        lines.append(f"🕒 Режим работы: {config.BUSINESS_HOURS}")

    if config.BUSINESS_FEATURES:
        lines.append("")
        lines.append("Почему выбирают нас:")
        for item in config.BUSINESS_FEATURES[:3]:
            lines.append(f"• {item}")

    return "\n".join(lines)


def build_contact_manager_text() -> str:
    if not config.MANAGERS:
        return "Сейчас менеджер недоступен. Попробуйте позже."

    manager_id = config.MANAGERS[0]
    manager_link = f"<a href=\"tg://user?id={manager_id}\">написать менеджеру</a>"
    return config.CONTACT_MANAGER_TEXT.format(
        manager_link=manager_link,
        manager_id=manager_id,
    )


async def notify_managers_contact_request(context: ContextTypes.DEFAULT_TYPE, user) -> None:
    client_id = user.id
    client_name = escape(user.first_name or "Клиент")
    client_link = f"<a href=\"tg://user?id={client_id}\">{client_name}</a>"
    username = f"@{escape(user.username)}" if user.username else "нет"
    text = config.MANAGER_CONTACT_REQUEST_TEXT.format(
        client_link=client_link,
        client_id=client_id,
        username=username,
    )

    for manager in config.MANAGERS:
        await context.bot.send_message(manager, text, parse_mode="HTML")


async def forward_client_message_to_managers(
    context: ContextTypes.DEFAULT_TYPE,
    user,
    message_text: str,
) -> None:
    client_id = user.id
    client_name = escape(user.first_name or "Клиент")
    client_link = f"<a href=\"tg://user?id={client_id}\">{client_name}</a>"
    username = f"@{escape(user.username)}" if user.username else "нет"

    text = config.MANAGER_CLIENT_MESSAGE_TEXT.format(
        client_link=client_link,
        client_id=client_id,
        username=username,
        message=escape(message_text),
    )

    for manager in config.MANAGERS:
        await context.bot.send_message(manager, text, parse_mode="HTML")


def parse_booking_datetime(date: str, time: str):
    return datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")


def estimate_upsell_total(service_name: str, upsell_details: str, comment: str) -> int:
    total = 0
    names = []

    if upsell_details:
        for line in upsell_details.splitlines():
            if " — " in line:
                names.append(line.split(" — ", 1)[0].strip("• "))
    elif "Доп. услуги:" in comment:
        tail = comment.split("Доп. услуги:", 1)[1]
        names = [item.strip() for item in tail.split(",") if item.strip()]

    for name in names:
        upsell = get_upsell_by_name(service_name, name)
        if upsell:
            total += upsell["price"]

    return total


def normalize_booking_financials(row):
    (
        booking_id,
        date,
        time,
        service,
        status,
        total_price,
        service_price,
        upsell_total,
        upsell_details,
        comment,
    ) = row

    service_info = get_service_by_name(service)
    normalized_service_price = service_price or (service_info["price"] if service_info else 0)
    normalized_upsell_total = upsell_total or estimate_upsell_total(service, upsell_details or "", comment or "")
    normalized_total = total_price or (normalized_service_price + normalized_upsell_total)

    return {
        "id": booking_id,
        "date": date,
        "time": time,
        "service": service,
        "status": status,
        "service_price": normalized_service_price,
        "upsell_total": normalized_upsell_total,
        "total_price": normalized_total,
        "upsell_details": upsell_details or "",
    }


def get_client_analytics(client_id: int, exclude_booking_id: Optional[int] = None):
    database.cursor.execute(
        """
        SELECT id, date, time, service, status, total_price, service_price, upsell_total, upsell_details, comment
        FROM bookings
        WHERE user_id=?
        ORDER BY date DESC, time DESC
        """,
        (client_id,),
    )
    rows = database.cursor.fetchall()

    now = datetime.datetime.now()
    visits = []
    total_revenue = 0

    for raw_row in rows:
        booking = normalize_booking_financials(raw_row)
        if booking["id"] == exclude_booking_id:
            continue
        if booking["status"] in INACTIVE_BOOKING_STATUSES:
            continue

        booking_dt = parse_booking_datetime(booking["date"], booking["time"])
        if booking_dt <= now:
            visits.append(booking)
            total_revenue += booking["total_price"]

    database.cursor.execute(
        """
        SELECT date, service FROM history
        WHERE user_id=?
        ORDER BY date DESC
        """,
        (client_id,),
    )
    legacy_rows = database.cursor.fetchall()

    lines = []
    for booking in visits[:10]:
        formatted_date = format_date_str_ru(booking["date"], include_year=True)
        lines.append(
            f"{formatted_date} {booking['time']} — {booking['service']} — {format_money(booking['total_price'])}₽"
        )
    for legacy in legacy_rows:
        if len(lines) >= 10:
            break
        lines.append(f"{format_date_str_ru(legacy[0], include_year=True)} — {legacy[1]}")

    visits_count = len(visits) + len(legacy_rows)
    history_text = "\n".join(lines) if lines else "Нет истории"
    return visits_count, history_text, total_revenue


def build_manager_message(data: dict, client_id: int, booking_id: int) -> str:
    service_price, _, total_price = calculate_booking_totals(data["draft_owner_id"])
    selected_upsells = data.get("selected_upsells", [])
    visits_count, history_text, previous_revenue = get_client_analytics(client_id, exclude_booking_id=booking_id)
    has_history = visits_count > 0 and history_text != "Нет истории"

    client_name = escape(data.get("client_first_name", "Клиент"))
    client_username = data.get("client_username")
    client_profile_link = f"<a href=\"tg://user?id={client_id}\">{client_name}</a>"
    client_id_link = f"<a href=\"tg://user?id={client_id}\">{client_id}</a>"
    username_line = f"@{escape(client_username)}" if client_username else "нет"

    lines = [
        config.MANAGER_NEW_BOOKING_TITLE,
        "",
        f"Имя: {escape(str(data.get('name', '')))}",
        f"Телефон: {escape(str(data.get('phone', '')))}",
        f"Марка авто: {escape(str(data.get('brand', '')))}",
        f"Модель авто: {escape(str(data.get('model', '')))}",
        f"Клиент: {client_profile_link}",
        f"ID клиента: {client_id_link}",
        f"Username: {username_line}",
        "",
        "🧾 Состав записи:",
        f"• {escape(data['service'])} — {format_money(service_price)}₽",
    ]

    if selected_upsells:
        for item in selected_upsells:
            lines.append(f"• {escape(item['name'])} — {format_money(item['price'])}₽")
    else:
        lines.append("• Доп. услуги не выбраны")

    lines.extend(
        [
            f"Итого по заявке: {format_money(total_price)}₽",
            "",
            f"Дата: {escape(str(data['date']))}",
            f"Время: {escape(str(data['time']))}",
            f"Комментарий: {escape(str(data.get('comment', '')))}",
        ]
    )

    if has_history:
        lines.extend(
            [
                "",
                f"{config.MANAGER_REVENUE_TITLE}:",
                f"Ранее принес: {format_money(previous_revenue)}₽",
                "",
                f"{config.MANAGER_HISTORY_TITLE}:",
                f"Посещений: {visits_count}",
                escape(history_text),
            ]
        )

    return "\n".join(lines)


def build_reminder_markup(booking_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(config.BUTTON_COMING, callback_data=f"client_coming_{booking_id}"),
                InlineKeyboardButton(config.BUTTON_CANCEL, callback_data=f"client_cancel_{booking_id}"),
            ],
            [InlineKeyboardButton(config.BUTTON_RESCHEDULE, callback_data=f"client_reschedule_{booking_id}")],
        ]
    )


async def send_main_menu_message(update: Update, text: Optional[str] = None):
    if maintenance_mode and update.message:
        await update.message.reply_text(
            "⚙️ Сейчас ведутся технические работы. Пожалуйста, свяжитесь с менеджером."
        )
        return

    name = get_client_name_for_message(update)
    message_text = text or build_main_menu_text(name=name)
    if update.message:
        await update.message.reply_text(message_text, reply_markup=build_main_menu_markup())


async def show_main_menu(query, user_id: int, name: Optional[str] = None):
    reset_booking_state(user_id)
    await query.edit_message_text(build_main_menu_text(name=name), reply_markup=build_main_menu_markup())


async def show_catalog(query, user_id: int):
    await query.edit_message_text(
        build_catalog_text(),
        reply_markup=build_catalog_markup(user_id),
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_main_menu_message(update, text=config.WELCOME_TEXT.format(company_name=config.COMPANY_NAME))


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data == "main_menu":
        await show_main_menu(query, user_id, name=query.from_user.first_name or "Клиент")
        return

    if data == "contact_manager":
        user_state[user_id] = "contact_message"
        await query.edit_message_text(
            f"{build_contact_manager_text()}\n\n{config.CONTACT_MANAGER_PROMPT_TEXT}",
            parse_mode="HTML",
            reply_markup=build_main_menu_markup(),
        )
        await notify_managers_contact_request(context, query.from_user)
        return

    if data == "show_catalog":
        if booking_is_active(user_id):
            touch_booking(user_id, query.from_user)
        await show_catalog(query, user_id)
        return

    if data == "resume_booking":
        if booking_is_active(user_id):
            touch_booking(user_id, query.from_user)
            await query.edit_message_text(config.BOOKING_INTRO_TEXT, reply_markup=build_service_keyboard())
        else:
            await query.edit_message_text(config.BOOKING_INTRO_TEXT, reply_markup=build_service_keyboard())
        return

    if data == "start_booking":
        start_booking_draft(query.from_user)
        await query.edit_message_text(config.BOOKING_INTRO_TEXT, reply_markup=build_service_keyboard())
        return

    if data.startswith("service_"):
        service_name = data.replace("service_", "", 1)
        service = get_service_by_name(service_name)
        if not service:
            await query.answer("Услуга не найдена.", show_alert=True)
            return

        if not booking_is_active(user_id):
            start_booking_draft(query.from_user)

        draft = user_data_temp[user_id]
        draft["service"] = service_name
        draft["selected_upsells"] = []
        touch_booking(user_id, query.from_user)
        await query.edit_message_text("Выберите дату:", reply_markup=build_date_keyboard())
        return

    if data.startswith("date_"):
        if not booking_is_active(user_id) or "service" not in user_data_temp[user_id]:
            await query.edit_message_text(config.BOOKING_INTRO_TEXT, reply_markup=build_service_keyboard())
            return

        days = int(data.replace("date_", "", 1))
        date = str(datetime.date.today() + datetime.timedelta(days=days))
        user_data_temp[user_id]["date"] = date
        touch_booking(user_id, query.from_user)

        markup, free_slots = build_time_keyboard(date)
        if not free_slots:
            await query.edit_message_text(
                "На выбранную дату свободного времени нет. Выберите другую дату:",
                reply_markup=build_date_keyboard(),
            )
            return

        await query.edit_message_text("Выберите время:", reply_markup=markup)
        return

    if data.startswith("time_"):
        if not booking_is_active(user_id):
            await query.edit_message_text(config.BOOKING_INTRO_TEXT, reply_markup=build_service_keyboard())
            return

        time = data.replace("time_", "", 1)
        selected_date = user_data_temp[user_id].get("date")
        if not selected_date:
            await query.edit_message_text("Сначала выберите дату.", reply_markup=build_date_keyboard())
            return

        if not is_time_available(selected_date, time):
            markup, free_slots = build_time_keyboard(selected_date)
            if free_slots:
                await query.answer("Это время уже занято, выберите другое.", show_alert=True)
                await query.edit_message_text("Это время занято. Выберите свободное:", reply_markup=markup)
            else:
                await query.answer("На эту дату мест больше нет.", show_alert=True)
                await query.edit_message_text(
                    "На выбранную дату мест больше нет. Выберите другую дату:",
                    reply_markup=build_date_keyboard(),
                )
            return

        user_data_temp[user_id]["time"] = time
        touch_booking(user_id, query.from_user)
        user_state[user_id] = "name"
        await query.edit_message_text("Введите ваше имя:", reply_markup=build_prompt_markup())
        return

    if data.startswith("upsell_"):
        if not booking_is_active(user_id) or "service" not in user_data_temp[user_id]:
            await query.edit_message_text(config.BOOKING_INTRO_TEXT, reply_markup=build_service_keyboard())
            return

        upsell_name = data.replace("upsell_", "", 1)
        draft = user_data_temp[user_id]
        upsell = get_upsell_by_name(draft["service"], upsell_name)
        if not upsell:
            await query.answer("Доп. услуга не найдена.", show_alert=True)
            return

        selected = draft.setdefault("selected_upsells", [])
        selected_names = {item["name"] for item in selected}
        if upsell_name in selected_names:
            draft["selected_upsells"] = [item for item in selected if item["name"] != upsell_name]
            await query.answer(f"Убрали: {upsell_name}")
        else:
            draft["selected_upsells"].append(upsell)
            await query.answer(f"Добавили: {upsell_name}")

        touch_booking(user_id, query.from_user)
        upsell_text, markup = build_upsell_prompt(user_id)
        await query.edit_message_text(upsell_text, reply_markup=markup)
        return

    if data == "confirm":
        if not booking_is_active(user_id):
            await query.edit_message_text(config.BOOKING_INTRO_TEXT, reply_markup=build_service_keyboard())
            return

        selected_date = user_data_temp[user_id].get("date")
        selected_time = user_data_temp[user_id].get("time")
        if selected_date and selected_time and not is_time_available(selected_date, selected_time):
            markup, free_slots = build_time_keyboard(selected_date)
            if free_slots:
                await query.edit_message_text(
                    "Пока вы заполняли заявку, выбранное время заняли. Выберите другое:",
                    reply_markup=markup,
                )
            else:
                await query.edit_message_text(
                    "Пока вы заполняли заявку, все слоты на эту дату заняли. Выберите другую дату:",
                    reply_markup=build_date_keyboard(),
                )
            return

        await send_to_manager(context, user_id)
        reset_booking_state(user_id)
        await query.edit_message_text(
            "✅ Вы записаны! Менеджер уже получил вашу заявку.",
            reply_markup=build_main_menu_markup(),
        )
        return

    if data.startswith("client_coming_"):
        booking_id = int(data.replace("client_coming_", "", 1))
        database.cursor.execute(
            """
            UPDATE bookings
            SET status='confirmed_by_client'
            WHERE id=? AND user_id=?
            """,
            (booking_id, user_id),
        )
        database.conn.commit()

        if database.cursor.rowcount:
            await query.edit_message_text("Спасибо! Отметили, что вы придете. До встречи.")
            for manager in config.MANAGERS:
                await context.bot.send_message(manager, f"✅ Клиент подтвердил визит. Заявка #{booking_id}")
        else:
            await query.answer("Эта запись не найдена или уже обработана.", show_alert=True)
        return

    if data.startswith("client_cancel_"):
        booking_id = int(data.replace("client_cancel_", "", 1))
        database.cursor.execute(
            """
            UPDATE bookings
            SET status='cancelled'
            WHERE id=? AND user_id=?
            """,
            (booking_id, user_id),
        )
        database.conn.commit()

        if database.cursor.rowcount:
            await query.edit_message_text("❌ Запись отменена. Если захотите, поможем подобрать другое время.")
            for manager in config.MANAGERS:
                await context.bot.send_message(manager, f"❌ Клиент отменил запись. Заявка #{booking_id}")
        else:
            await query.answer("Эта запись не найдена или уже обработана.", show_alert=True)
        return

    if data.startswith("client_reschedule_"):
        booking_id = int(data.replace("client_reschedule_", "", 1))
        database.cursor.execute(
            """
            UPDATE bookings
            SET status='reschedule_requested'
            WHERE id=? AND user_id=?
            """,
            (booking_id, user_id),
        )
        database.conn.commit()

        if database.cursor.rowcount:
            await query.edit_message_text(
                "🔁 Запрос на перенос принят. Нажмите «Записаться», чтобы выбрать новую дату и время.",
                reply_markup=build_main_menu_markup(),
            )
            for manager in config.MANAGERS:
                await context.bot.send_message(manager, f"🔁 Клиент попросил перенос. Заявка #{booking_id}")
        else:
            await query.answer("Эта запись не найдена или уже обработана.", show_alert=True)
        return


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    state = user_state.get(user_id)

    if booking_is_active(user_id):
        touch_booking(user_id, update.effective_user)

    if not state:
        await send_main_menu_message(update)
        return

    if state == "contact_message":
        await forward_client_message_to_managers(context, update.effective_user, text)
        user_state.pop(user_id, None)
        await update.message.reply_text(
            "✅ Сообщение отправлено менеджеру. Скоро с вами свяжутся.",
            reply_markup=build_main_menu_markup(),
        )
        return

    if state == "name":
        user_data_temp[user_id]["name"] = text
        user_state[user_id] = "phone"
        await update.message.reply_text("Введите телефон:", reply_markup=build_prompt_markup())
        return

    if state == "phone":
        user_data_temp[user_id]["phone"] = text
        user_state[user_id] = "brand"
        await update.message.reply_text("Марка авто:", reply_markup=build_prompt_markup())
        return

    if state == "brand":
        user_data_temp[user_id]["brand"] = text
        user_state[user_id] = "model"
        await update.message.reply_text("Модель авто:", reply_markup=build_prompt_markup())
        return

    if state == "model":
        user_data_temp[user_id]["model"] = text
        user_state[user_id] = "comment"
        await update.message.reply_text("Комментарий (если есть):", reply_markup=build_prompt_markup())
        return

    if state == "comment":
        user_data_temp[user_id]["comment"] = text
        user_state.pop(user_id, None)
        upsell_text, markup = build_upsell_prompt(user_id)
        await update.message.reply_text(upsell_text, reply_markup=markup)
        return


async def send_to_manager(context, user_id: int):
    data = user_data_temp[user_id]
    client_id = data.get("client_id", user_id)
    data["draft_owner_id"] = user_id

    database.cursor.execute(
        """
        INSERT OR REPLACE INTO clients (user_id, name, phone, car_brand, car_model)
        VALUES (?, ?, ?, ?, ?)
        """,
        (client_id, data["name"], data["phone"], data["brand"], data["model"]),
    )

    service_price, upsell_total, total_price = calculate_booking_totals(user_id)
    upsell_lines = [f"{item['name']} — {item['price']}" for item in data.get("selected_upsells", [])]
    upsell_details = "\n".join(upsell_lines)

    comment_for_db = data.get("comment", "")
    if data.get("selected_upsells"):
        selected_names = ", ".join(item["name"] for item in data["selected_upsells"])
        comment_for_db = f"{comment_for_db}\nДоп. услуги: {selected_names}".strip()

    database.cursor.execute(
        """
        INSERT INTO bookings (
            user_id, service, date, time, status, comment,
            service_price, upsell_details, upsell_total, total_price
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            client_id,
            data["service"],
            data["date"],
            data["time"],
            "booked",
            comment_for_db,
            service_price,
            upsell_details,
            upsell_total,
            total_price,
        ),
    )
    booking_id = database.cursor.lastrowid
    database.conn.commit()

    message = build_manager_message(data, client_id, booking_id)
    for manager in config.MANAGERS:
        await context.bot.send_message(chat_id=manager, text=message, parse_mode="HTML")


async def maybe_send_incomplete_booking_reminders(app: Application, now: datetime.datetime):
    for user_id, draft in list(user_data_temp.items()):
        if not draft.get("booking_started"):
            continue
        if draft.get("inactivity_reminder_sent"):
            continue

        last_activity_raw = draft.get("last_activity")
        if not last_activity_raw:
            continue

        last_activity = datetime.datetime.fromisoformat(last_activity_raw)
        minutes_idle = (now - last_activity).total_seconds() / 60
        if minutes_idle < config.BOOKING_HOLD_MINUTES:
            continue

        name = draft.get("name") or draft.get("client_first_name") or "Клиент"
        await app.bot.send_message(
            user_id,
            config.ABANDONED_BOOKING_TEXT.format(name=name),
            reply_markup=build_main_menu_markup(),
        )
        draft["inactivity_reminder_sent"] = True


def get_weekly_report_metrics(now: datetime.datetime):
    week_ago = now - datetime.timedelta(days=7)
    database.cursor.execute(
        """
        SELECT id, date, time, service, status, total_price, service_price, upsell_total, upsell_details, comment
        FROM bookings
        ORDER BY date DESC, time DESC
        """
    )
    rows = database.cursor.fetchall()

    bookings_count = 0
    total_revenue = 0
    upsell_revenue = 0

    for raw_row in rows:
        booking = normalize_booking_financials(raw_row)
        if booking["status"] in INACTIVE_BOOKING_STATUSES:
            continue

        booking_dt = parse_booking_datetime(booking["date"], booking["time"])
        if week_ago <= booking_dt <= now:
            bookings_count += 1
            total_revenue += booking["total_price"]
            upsell_revenue += booking["upsell_total"]

    return bookings_count, total_revenue, upsell_revenue


async def maybe_send_weekly_report(app: Application, now: datetime.datetime):
    if now.weekday() != config.WEEKLY_REPORT_WEEKDAY:
        return
    if now.hour != config.WEEKLY_REPORT_HOUR:
        return
    if now.minute > 4:
        return

    period_key = now.date().isoformat()
    if get_meta("last_weekly_report") == period_key:
        return

    bookings_count, total_revenue, upsell_revenue = get_weekly_report_metrics(now)
    report_text = (
        f"{config.MANAGER_WEEKLY_REPORT_TITLE}\n\n"
        f"Записей: {bookings_count}\n"
        f"Выручка: {format_money(total_revenue)}₽\n"
        f"Дополнительные услуги: {format_money(upsell_revenue)}₽"
    )

    for manager in config.MANAGERS:
        await app.bot.send_message(manager, report_text)

    set_meta("last_weekly_report", period_key)


async def reminder_loop(app: Application):
    while True:
        now = datetime.datetime.now()

        database.cursor.execute(
            """
            SELECT id, user_id, date, time, reminder_24_sent, reminder_2_sent
            FROM bookings
            WHERE status IN (?, ?, ?, ?)
            """,
            ACTIVE_BOOKING_STATUSES,
        )
        bookings = database.cursor.fetchall()

        for booking_id, user_id, date, time, reminder_24_sent, reminder_2_sent in bookings:
            booking_time = parse_booking_datetime(date, time)
            hours_left = (booking_time - now).total_seconds() / 3600

            if (not reminder_24_sent) and 23.5 < hours_left < 24.5:
                await app.bot.send_message(user_id, config.REMINDER_24H_TEXT.format(time=time))
                database.cursor.execute(
                    "UPDATE bookings SET reminder_24_sent=1 WHERE id=?",
                    (booking_id,),
                )
                database.conn.commit()

            if (not reminder_2_sent) and 1.5 < hours_left < 2.5:
                await app.bot.send_message(
                    user_id,
                    config.REMINDER_2H_TEXT.format(time=time),
                    reply_markup=build_reminder_markup(booking_id),
                )
                database.cursor.execute(
                    "UPDATE bookings SET reminder_2_sent=1 WHERE id=?",
                    (booking_id,),
                )
                database.conn.commit()

        await maybe_send_incomplete_booking_reminders(app, now)
        await maybe_send_weekly_report(app, now)
        await asyncio.sleep(60)


def main():
    app = Application.builder().token(config.TOKEN).build()
    app.job_queue.run_once(lambda ctx: asyncio.create_task(reminder_loop(app)), 1)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
