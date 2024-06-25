"""Handlers for telegram bot."""

import asyncio
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from aiogram import Bot
from aiogram.filters.command import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from clinic_app.backend.csv_files import CSVFile, Database
from clinic_app.backend.utils import format_phone
from clinic_app.frontend.telegram_bot.constants import dp
from clinic_app.frontend.telegram_bot.keyboard.reply import yes_no
from clinic_app.frontend.telegram_bot.keyboard.reply.phone import (
    get_phone_markup,
)
from clinic_app.frontend.telegram_bot.states import UserStates
from clinic_app.shared import CSVS
from loguru import logger
from zoneinfo import ZoneInfo

if TYPE_CHECKING:
    import pandas as pd


MANAGER_ID = 195305791


def register_handlers() -> None:
    """View handlers and report it into log message."""
    logger.info("Handlers have been successfully registered!")


@dp.message(CommandStart())
async def on_start(msg: Message, state: FSMContext) -> None:
    """Entrypoint of the bot."""
    db = Database()
    if db.value_exists(msg.from_user.id, "tg_user_id"):
        await msg.answer(
            "Вы уже зарегистрированы в системе. Мы вам напомним о вашей "
            "записи",
            parse_mode=None,
        )
        return

    name = msg.from_user.first_name

    await state.set_state(UserStates.get_phone)
    mp = get_phone_markup().as_markup(resize_keyboard=True)
    await msg.answer(
        rf"Приветствую {name}\! Пришлите ваш номер телефона", reply_markup=mp
    )


@dp.message(UserStates.get_phone)
async def get_phone(msg: Message, state: FSMContext) -> None:
    """Get phone from user."""
    if not msg.contact:
        await msg.answer("Вы не отправили свой номер телефона")
        return

    phone = msg.contact.phone_number
    db = Database()

    if not db.value_exists(msg.from_user.id, "tg_user_id"):
        df = db.get_df()
        row = {
            "phone": format_phone(phone),
            "tg_user_id": msg.from_user.id,
            "tg_username": msg.from_user.username,
        }
        df.loc[len(df)] = row
        df.to_csv(db.path, index=False)

    await msg.answer(
        r"Ваш номер телефона сохранен\. Мы вам напомним о вашей записи",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.clear()


@dp.message(UserStates.notify_tommorow)
async def notify_tommorow_dialog(msg: Message, state: FSMContext) -> None:
    """Remind me the day before your appointment."""
    if msg.text not in ["Да", "Нет"]:
        await msg.answer("Нет такого варианта ответа")
        return

    data = await state.get_data()
    info: pd.Series = data["info_data"]
    csv: CSVFile = data["csv"]

    if msg.text == "Да":
        df = csv.get_df()
        df.loc[info.name, "Подтверждение"] = 1
        df.to_csv(csv.path, index=False)

        await msg.answer(
            f"Отлично! Ждем вас в <b>{info["ДатаНачала"]}</b>",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.clear()

    elif msg.text == "Нет":
        df = csv.get_df()
        df.loc[info.name, "Подтверждение"] = -1
        df.to_csv(csv.path, index=False)

        reply_markup = yes_no().as_markup(resize_keyboard=True)

        await msg.answer(
            "Перезаписать вас на другое время?",
            reply_markup=reply_markup,
            parse_mode=None,
        )
        await state.set_state(UserStates.rescheduling)


async def notify_rescheduling(msg: Message, text: str) -> None:
    """Call this function by the scheduler."""
    await msg.answer(text, parse_mode=None)


@dp.message(UserStates.rescheduling)
async def reschedule(msg: Message, state: FSMContext, bot: Bot) -> None:
    """
    Conversation with the user about rescheduling an appointment with
    a doctor.
    """
    if msg.text not in ["Да", "Нет"]:
        await msg.answer("Нет такого варианта ответа")
        return

    data = await state.get_data()
    info: pd.Series = data["info_data"]
    csv: CSVFile = data["csv"]

    if msg.text == "Да":
        df = csv.get_df()
        df.loc[info.name, "Перезапись"] = 1
        df.loc[info.name, "Подтверждение"] = -1
        df.to_csv(csv.path, index=False)

        await msg.answer("Скоро вам позвонит менеджер для перезаписи")

        time = datetime.now().astimezone(ZoneInfo("Europe/Moscow"))
        text = (
            "НУЖНО ПЕРЕНАЗНАЧИТЬ ОЧЕРЕДЬ КЛИЕНТУ 🔴🔴🔴:\n"
            f"Клиент: @{msg.from_user.username}\n"
            f"Время по МСК: <b>{time}</b>\n"
            f"Сообщение:\n<b><i>{msg.text}</i></b>"
        )
        await bot.send_message(MANAGER_ID, text, parse_mode="HTML")

        client_id = "1377cb96-cf0b-4599-a213-67315c8c1966"
        doctor_id = info["ИДВрач"]
        clinic_id = info["ИДФилиал"]
        url = (
            "https://medapi.1cbit.ru/online_record"
            f"/client/{client_id}/doctor/{doctor_id}?clinic={clinic_id}"
        )
        await msg.answer(
            r"Спасибо, что предупредили\! Пожалуйста, перезапишитесь по "
            f"этой [ссылке]({url})",
            reply_markup=ReplyKeyboardRemove(),
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
            args=(msg, text),
        )
        sch.start()

    elif msg.text == "Нет":
        df = csv.get_df()
        df.loc[info.name, "Перезапись"] = -1
        df.to_csv(csv.path, index=False)

        await msg.answer(
            "Спасибо, что предупредили, будем вас ждать!",
            parse_mode=None,
            reply_markup=ReplyKeyboardRemove(),
        )

    await state.clear()


@dp.message(UserStates.review)
async def review(msg: Message, state: FSMContext) -> None:
    """Converstation with user about his feedback and review."""
    if msg.text not in list(map(str, range(1, 5 + 1))):
        await msg.answer("Оцените нас пожалуйста от 1 до 5!", parse_mode=None)
        return

    if msg.text == "5":
        url = "https://yandex.ru"
        await msg.answer(
            rf"Отлично, оцените нас на [Яндекс\.Картах]({url}) на карточку "
            "компании"
        )

        data = await state.get_data()
        reviews = CSVFile(CSVS["reviews"])

        row: pd.Series = data["row"]
        reviews.find_and_replace(
            search_value_column_name="Телефон",
            search_value=row["Телефон"],
            new_value_column_name="Отзыв",
            new_value=msg.text,
            save=True,
        )

        await asyncio.sleep(2)
        await msg.answer("Спасибо вам большое за отзыв!", parse_mode=None)
        await state.clear()

    else:
        await msg.answer(
            "Ого! Мы сожалеем! Расскажите нам, что мы можем улучшить! "
            "Мы примем меры!",
            parse_mode=None,
        )
        await state.update_data(review=msg.text)
        await state.set_state(UserStates.get_review)


@dp.message(UserStates.get_review)
async def get_review(msg: Message, state: FSMContext, bot: Bot) -> None:
    """Get full negative review from user and write it to csv file."""
    data = await state.get_data()
    db = Database()
    reviews = CSVFile(CSVS["reviews"])

    date = datetime.now().astimezone(ZoneInfo("Europe/Moscow")).date()
    phone = db.get_value_by_kv(
        kv=("tg_user_id", msg.from_user.id), column="phone"
    )

    review = f"{date}:{data["review"]}:{msg.text}:{phone}"
    time = datetime.now().astimezone(ZoneInfo("Europe/Moscow"))

    text = (
        "КЛИЕНТ ОСТАВИЛ ОТЗЫВ 🔴🔴🔴:\n"
        f"Клиент: @{msg.from_user.username}\n"
        f"Время по МСК: <b>{time}</b>\n"
        f"Отзыв:\n<b><i>{review}</i></b>"
    )
    await bot.send_message(MANAGER_ID, text, parse_mode="HTML")

    row: pd.Series = data["row"]
    reviews.find_and_replace(
        search_value_column_name="Телефон",
        search_value=row["Телефон"],
        new_value_column_name="Отзыв",
        new_value=review,
        save=True,
    )

    await asyncio.sleep(1.5)
    await msg.answer("Спасибо вам большое за отзыв!", parse_mode=None)
    await state.clear()
