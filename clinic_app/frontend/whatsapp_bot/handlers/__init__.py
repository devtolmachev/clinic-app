"""Handlers for whatsapp bot."""

import time
from datetime import datetime, timedelta
from types import FunctionType
from typing import TYPE_CHECKING, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from clinic_app.backend.csv_files import CSVFile, Database
from clinic_app.backend.utils import format_phone
from clinic_app.frontend.whatsapp_bot.constants import bot
from clinic_app.frontend.whatsapp_bot.states import (
    MainFSM,
    WhatsappFSMContext,
    get_fsm,
)
from clinic_app.shared import CSVS
from loguru import logger
from zoneinfo import ZoneInfo

if TYPE_CHECKING:
    import pandas as pd

MANAGER_ID = "972549102077@c.us"


def error_handler(f: FunctionType) -> Any:
    """Error handler."""

    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.exception(e)

    return wrapper


@error_handler
def middleware(type_webhook: str, body: dict) -> None:
    """FSM middleware."""
    if type_webhook == "incomingMessageReceived":
        msg = body.get("messageData")
        sender = body.get("senderData")
        if not msg or not sender:
            return

        if msg["textMessageData"]["textMessage"] == "/start":
            return on_start(body)
        
        fsm_context = get_fsm()
        fsm_state = fsm_context.get_state(sender["chatId"])

        if not fsm_state:
            return

        if fsm_state == MainFSM.get_phone:
            return get_phone(body, fsm_context)
        if fsm_state == MainFSM.get_review:
            return get_review(body, fsm_context)
        if fsm_state == MainFSM.notify_tommorow:
            return notify_tomorrow(body, fsm_context)
        if fsm_state == MainFSM.rescheduling:
            return rescheduling(body, fsm_context)
        if fsm_state == MainFSM.review:
            return on_review(body, fsm_context)


def resolve_chat_id(body_message: dict) -> int:
    """Get chat id from body message."""
    return body_message["senderData"]["chatId"]


def resolve_text_msg(body_message: dict) -> str:
    """Get text of message from body."""
    return body_message["messageData"]["textMessageData"]["textMessage"]


def get_phone_from_msg(body_message: dict) -> str:
    """Get phone from message."""
    return body_message["senderData"]["sender"].split("@")[0]


def on_start(body_msg: str) -> None:
    """Entrypoint of the bot."""
    db = Database()
    chat_id = resolve_chat_id(body_msg)
    if db.value_exists(chat_id, "wh_user_id"):
        bot.sending.sendMessage(
            chat_id,
            "Вы уже зарегистрированы в системе. Мы вам напомним о вашей "
            "записи",
        )
        return

    name = body_msg["senderData"]["senderName"]
    chat_id = resolve_chat_id(body_msg)

    get_fsm().set_state(MainFSM.get_phone, chat_id)
    bot.sending.sendMessage(
        chat_id, f"Приветствую {name}! Пришлите ваш номер телефона"
    )


def get_phone(body_msg: dict, state: WhatsappFSMContext) -> None:
    """Get phone from user."""
    phone = format_phone(resolve_text_msg(body_msg))
    if not phone:
        bot.sending.sendMessage(
            resolve_chat_id(body_msg), "Вы не отправили свой номер телефона"
        )
        return

    db = Database()

    if not db.value_exists(phone, "phone"):
        df = db.get_df()
        row = {
            "phone": format_phone(phone),
            "wh_user_id": resolve_chat_id(body_msg),
        }
        df.loc[len(df)] = row
        df.to_csv(db.path, index=False)

    bot.sending.sendMessage(
        resolve_chat_id(body_msg),
        "Ваш номер телефона сохранен. Мы вам напомним о вашей записи",
    )
    state.clear(resolve_chat_id(body_msg))


def get_review(body_msg: dict, state: WhatsappFSMContext) -> None:
    """Get full negative review from user and write it to csv file."""
    msg_text = resolve_text_msg(body_msg)
    chat_id = resolve_chat_id(body_msg)

    data = state.get_data(chat_id)
    db = Database()
    reviews = CSVFile(CSVS["reviews"])

    date = datetime.now().astimezone(ZoneInfo("Europe/Moscow")).date()
    phone = db.get_value_by_kv(kv=("wh_user_id", chat_id), column="phone")

    review = f"{date}:{data["review"]}:{msg_text}:{phone}"
    dt = datetime.now().astimezone(ZoneInfo("Europe/Moscow"))

    text = (
        "КЛИЕНТ ОСТАВИЛ ОТЗЫВ 🔴🔴🔴:\n"
        f"Клиент: {phone}\n"
        f"Время по МСК: {dt}\n"
        f"Сообщение:\n{resolve_text_msg(body_msg)}"
    )
    bot.sending.sendMessage(MANAGER_ID, text)

    row: pd.Series = data["row"]
    reviews.find_and_replace(
        search_value_column_name="Телефон",
        search_value=row["Телефон"],
        new_value_column_name="Отзыв",
        new_value=review,
        save=True,
    )

    time.sleep(1.5)
    bot.sending.sendMessage(chat_id, "Спасибо вам большое за отзыв!")
    state.clear(chat_id)


def notify_tomorrow(body_msg: dict, state: WhatsappFSMContext) -> None:
    """Remind me the day before your appointment."""
    chat_id = resolve_chat_id(body_msg)
    msg_text = resolve_text_msg(body_msg)
    if msg_text.lower() not in ["да", "нет"]:
        bot.sending.sendMessage(
            chat_id,
            "Нет такого варианта ответа, напишите пожалуйста `да` или `нет`"
        )
        return

    data = state.get_data(chat_id)
    info: pd.Series = data["info_data"]
    csv: CSVFile = data["csv"]

    if msg_text.lower() == "да":
        df = csv.get_df()
        df.loc[info.name, "Подтверждение"] = 1
        df.to_csv(csv.path, index=False)

        bot.sending.sendMessage(
            chat_id,
            f"Отлично! Ждем вас в {info["ДатаНачала"]}",
        )
        state.clear(chat_id)

    elif msg_text.lower() == "нет":
        df = csv.get_df()
        df.loc[info.name, "Подтверждение"] = -1
        df.to_csv(csv.path, index=False)

        bot.sending.sendMessage(
            chat_id,
            "Перезаписать вас на другое время? Отвечайте `да` или `нет`",
        )
        state.set_state(MainFSM.rescheduling, chat_id)


def rescheduling(body_msg: dict, state: WhatsappFSMContext) -> None:
    """
    Conversation with the user about rescheduling an appointment with
    a doctor.
    """
    msg_text = resolve_text_msg(body_msg)
    chat_id = resolve_chat_id(body_msg)
    if msg_text.lower() not in ["да", "нет"]:
        bot.sending.sendMessage(chat_id, "Нет такого варианта ответа")
        return

    data = state.get_data(chat_id)
    info: pd.Series = data["info_data"]
    csv: CSVFile = data["csv"]

    if msg_text.lower() == "да":
        df = csv.get_df()
        df.loc[info.name, "Перезапись"] = 1
        df.loc[info.name, "Подтверждение"] = -1
        df.to_csv(csv.path, index=False)

        bot.sending.sendMessage(
            chat_id, "Скоро вам позвонит менеджер для перезаписи"
        )

        time = datetime.now().astimezone(ZoneInfo("Europe/Moscow"))
        phone = get_phone_from_msg(body_msg)
        text = (
            "НУЖНО ПЕРЕНАЗНАЧИТЬ ОЧЕРЕДЬ КЛИЕНТУ 🔴🔴🔴:\n"
            f"Клиент: {phone}\n"
            f"Время по МСК: {time}\n"
            f"Сообщение:\n{resolve_text_msg(body_msg)}"
        )
        bot.sending.sendMessage(MANAGER_ID, text)

        client_id = "1377cb96-cf0b-4599-a213-67315c8c1966"
        doctor_id = info["ИДВрач"]
        clinic_id = info["ИДФилиал"]
        url = (
            "https://medapi.1cbit.ru/online_record"
            f"/client/{client_id}/doctor/{doctor_id}?clinic={clinic_id}"
        )
        bot.sending.sendMessage(
            chat_id,
            "Спасибо, что предупредили! Пожалуйста, перезапишитесь по "
            f"этой ссылке: {url}",
        )

        schedule_date = datetime.now() + timedelta(minutes=15)
        sch = AsyncIOScheduler()
        text = (
            "Если у вас не получилось записаться онлайн вы можете "
            "записаться по номеру телефона: 123456"
        )
        sch.add_job(
            notify_rescheduling,
            "date",
            run_date=schedule_date,
            args=(msg_text, chat_id),
        )
        sch.start()

    elif msg_text.lower() == "нет":
        df = csv.get_df()
        df.loc[info.name, "Перезапись"] = -1
        df.to_csv(csv.path, index=False)

        bot.sending.sendMessage(
            chat_id, "Спасибо, что предупредили, будем вас ждать!"
        )

    state.clear(chat_id)


def on_review(body_msg: dict, state: WhatsappFSMContext) -> None:
    """Converstation with user about his feedback and review."""
    chat_id = resolve_chat_id(body_msg)
    msg_text = resolve_text_msg(body_msg)
    if msg_text not in list(map(str, range(1, 5 + 1))):
        bot.sending.sendMessage(chat_id, "Оцените нас пожалуйста от 1 до 5!")
        return

    if msg_text == "5":
        url = "https://yandex.ru"
        bot.sending.sendMessage(
            chat_id,
            f"Отлично, оцените нас на Яндекс.Картах {url} на карточку "
            "компании",
        )

        data = state.get_data(chat_id)
        reviews = CSVFile(CSVS["reviews"])

        row: pd.Series = data["row"]
        reviews.find_and_replace(
            search_value_column_name="Телефон",
            search_value=row["Телефон"],
            new_value_column_name="Отзыв",
            new_value=msg_text,
            save=True,
        )

        time.sleep(2)
        bot.sending.sendMessage(chat_id, "Спасибо вам большое за отзыв!")
        state.clear(chat_id)

    else:
        bot.sending.sendMessage(
            chat_id,
            "Ого! Мы сожалеем! Расскажите нам, что мы можем улучшить! "
            "Мы примем меры!",
        )
        state.update_data(chat_id, review=msg_text)
        state.set_state(MainFSM.get_review, chat_id)


def notify_rescheduling(text: str, chat_id: int) -> None:
    """Call this function by the scheduler."""
    bot.sending.sendMessage(chat_id, text)
