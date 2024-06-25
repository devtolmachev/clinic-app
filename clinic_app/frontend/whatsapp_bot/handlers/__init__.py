"""Handlers for whatsapp bot."""

import time
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from whatsapp_chatbot_python import Notification

from clinic_app.backend.csv_files import CSVFile, Database
from clinic_app.backend.utils import format_phone
from clinic_app.frontend.whatsapp_bot.constants import bot
from clinic_app.frontend.whatsapp_bot.states import (
    WhStates,
)
from clinic_app.shared import CSVS
from loguru import logger
from zoneinfo import ZoneInfo

if TYPE_CHECKING:
    import pandas as pd

MANAGER_ID = "972549102077@c.us"


def run_work():
    logger.info("Register whatsapp handlers was successfully!")


def resolve_chat_id(body_message: dict) -> int:
    """Get chat id from body message."""
    return body_message["senderData"]["chatId"]


def resolve_text_msg(body_message: dict) -> str:
    """Get text of message from body."""
    try:
        return body_message["messageData"]["textMessageData"]["textMessage"]
    except KeyError:
        return body_message["messageData"]["extendedTextMessageData"]["text"]


def get_phone_from_msg(body_message: dict) -> str:
    """Get phone from message."""
    return body_message["senderData"]["sender"].split("@")[0]


@bot.router.message(text_message="/start")
def on_start(notification: Notification) -> None:
    """Entrypoint of the bot."""
    db = Database()
    chat_id = notification.chat

    if db.value_exists(chat_id, "wh_user_id"):
        notification.answer(
            "Вы уже зарегистрированы в системе. Мы вам напомним о вашей "
            "записи",
        )
        return

    phone = format_phone(get_phone_from_msg(notification.event))
    db = Database()

    if not db.value_exists(chat_id, "wh_user_id"):
        df = db.get_df()
        row = {
            "phone": phone,
            "wh_user_id": chat_id,
        }
        df.loc[len(df)] = row
        df.to_csv(db.path, index=False)

    notification.answer(
        "Ваш номер телефона сохранен. Мы вам напомним о вашей записи",
    )


@bot.router.message(state=WhStates.get_review)
def get_review(notification: Notification) -> None:
    """Get full negative review from user and write it to csv file."""
    msg_text = notification.message_text
    chat_id = notification.chat

    data = notification.state_manager.get_state_data(notification.sender)
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
        f"Сообщение:\n{msg_text}"
    )
    bot.api.sending.sendMessage(MANAGER_ID, text)

    row: pd.Series = data["row"]
    reviews.find_and_replace(
        search_value_column_name="Телефон",
        search_value=row["Телефон"],
        new_value_column_name="Отзыв",
        new_value=review,
        save=True,
    )

    time.sleep(1.5)
    notification.answer("Спасибо вам большое за отзыв!")
    notification.state_manager.delete_state(notification.sender)


@bot.router.message(state=WhStates.notify_tommorow)
def notify_tomorrow(notification: Notification) -> None:
    """Remind me the day before your appointment."""
    msg_text = notification.message_text
    if msg_text.lower() not in ["да", "нет"]:
        notification.answer(
            "Нет такого варианта ответа, напишите пожалуйста `да` или `нет`",
        )
        return

    data = notification.state_manager.get_state_data(notification.sender)
    info: pd.Series = data["info_data"]
    csv: CSVFile = data["csv"]

    if msg_text.lower() == "да":
        df = csv.get_df()
        df.loc[info.name, "Подтверждение"] = 1
        df.to_csv(csv.path, index=False)

        notification.answer(
            f"Отлично! Ждем вас в {info["ДатаНачала"]}",
        )
        notification.state_manager.delete_state(notification.sender)

    elif msg_text.lower() == "нет":
        df = csv.get_df()
        df.loc[info.name, "Подтверждение"] = -1
        df.to_csv(csv.path, index=False)

        notification.answer(
            "Перезаписать вас на другое время? Отвечайте `да` или `нет`",
        )
        notification.state_manager.set_state(
            notification.sender, WhStates.rescheduling
        )
        notification.state_manager.set_state_data(
            notification.sender, data
        )


@bot.router.message(state=WhStates.rescheduling)
def rescheduling(notification: Notification) -> None:
    """
    Conversation with the user about rescheduling an appointment with
    a doctor.
    """
    chat_id = notification.chat
    msg_text = notification.message_text
    if msg_text.lower() not in ["да", "нет"]:
        notification.answer("Нет такого варианта ответа")
        return

    data = notification.state_manager.get_state_data(notification.sender)
    info: pd.Series = data["info_data"]
    csv: CSVFile = data["csv"]

    if msg_text.lower() == "да":
        df = csv.get_df()
        df.loc[info.name, "Перезапись"] = 1
        df.loc[info.name, "Подтверждение"] = -1
        df.to_csv(csv.path, index=False)

        notification.answer("Скоро вам позвонит менеджер для перезаписи")

        time = datetime.now().astimezone(ZoneInfo("Europe/Moscow"))
        phone = get_phone_from_msg(notification.event)
        text = (
            "НУЖНО ПЕРЕНАЗНАЧИТЬ ОЧЕРЕДЬ КЛИЕНТУ 🔴🔴🔴:\n"
            f"Клиент: {phone}\n"
            f"Время по МСК: {time}\n"
            f"Сообщение:\n{notification.message_text}"
        )
        bot.api.sending.sendMessage(MANAGER_ID, text)

        client_id = "1377cb96-cf0b-4599-a213-67315c8c1966"
        doctor_id = info["ИДВрач"]
        clinic_id = info["ИДФилиал"]
        url = (
            "https://medapi.1cbit.ru/online_record"
            f"/client/{client_id}/doctor/{doctor_id}?clinic={clinic_id}"
        )
        notification.answer(
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

        notification.answer("Спасибо, что предупредили, будем вас ждать!")

    notification.state_manager.delete_state(notification.sender)


@bot.router.message(state=WhStates.review)
def on_review(notification: Notification) -> None:
    """Converstation with user about his feedback and review."""
    msg_text = notification.message_text
    if msg_text not in list(map(str, range(1, 5 + 1))):
        notification.answer("Оцените нас пожалуйста от 1 до 5!")
        return

    data = notification.state_manager.get_state_data(notification.sender)

    if msg_text == "5":
        url = "https://yandex.ru"
        notification.answer(
            f"Отлично, оцените нас на Яндекс.Картах {url} на карточку "
            "компании",
        )

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
        notification.answer("Спасибо вам большое за отзыв!")
        notification.state_manager.delete_state(notification.sender)

    else:
        notification.answer(
            "Ого! Мы сожалеем! Расскажите нам, что мы можем улучшить! "
            "Мы примем меры!",
        )
        data["review"] = msg_text
        notification.state_manager.set_state(
            notification.sender, WhStates.get_review
        )
        notification.state_manager.set_state_data(
            notification.sender, data
        )


def notify_rescheduling(text: str, chat_id: int) -> None:
    """Call this function by the scheduler."""
    bot.api.sending.sendMessage(chat_id, text)
