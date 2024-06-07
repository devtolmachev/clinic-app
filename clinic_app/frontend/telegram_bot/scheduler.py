from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from aiogram.types import ReplyKeyboardRemove
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from clinic_app.backend.csv_files import CSVFile, Database
from clinic_app.backend.utils import format_phone
from clinic_app.frontend.telegram_bot.contants import bot
from clinic_app.frontend.telegram_bot.keyboard.reply import yes_no
from clinic_app.frontend.telegram_bot.states import UserStates, get_fsm
from clinic_app.shared import CSVS
from zoneinfo import ZoneInfo

if TYPE_CHECKING:
    from pandas import Series


def get_user_id(row: Series) -> int | None:
    """Get user id from database csv file by phone."""
    db = Database()
    phone = format_phone(row["Телефон"])
    return db.get_value_by_kv(("phone", phone), "tg_user_id")


async def check_csvs() -> None:
    """Check csv and start work with users."""
    tasks = []

    tommorow = CSVFile(CSVS["tommorow"])
    two_hours = CSVFile(CSVS["2hours"])
    reviews = CSVFile(CSVS["reviews"])

    for index, row in tommorow.get_df().iterrows():
        tasks.append(notify_before_day(row=row, csv=tommorow))

    for index, row in two_hours.get_df().iterrows():
        tasks.append(notify_before_2hours(row=row, csv=two_hours))

    for index, row in reviews.get_df().iterrows():
        tasks.append(notify_review(row=row, csv=reviews))

    await asyncio.gather(*tasks)


async def notify_before_day(row: Series, csv: CSVFile) -> None:
    """Notify before day work.

    Interact with `tomorrow.csv` file
    """
    user_id = get_user_id(row=row)
    if not user_id:
        return

    reply_markup = yes_no().as_markup(resize_keyboard=True)
    await bot.send_message(
        user_id,
        f"Вы записались на <b>{row["ВремяНачала"]}</b>, подтверждаете запись?",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )

    state = get_fsm(bot_id=bot.id, user_id=user_id, chat_id=user_id)
    await state.set_state(UserStates.notify_tommorow)
    await state.update_data(info_data=row, csv=csv)


async def notify_before_2hours(row: Series, csv: CSVFile) -> None:
    """Notify before 2 hours work.

    Interact with `2hours.csv` file
    """
    user_id = get_user_id(row=row)
    if not user_id:
        return

    await bot.send_message(
        user_id,
        "Ждем вас сегодня в время по адресу! Будем рады вас видеть",
        parse_mode=None,
        reply_markup=ReplyKeyboardRemove(),
    )


async def notify_review(row: Series, csv: CSVFile) -> None:
    """Notify add review work.

    Interact with `Reviews.csv` file
    """
    user_id = get_user_id(row=row)
    if not user_id:
        return

    await bot.send_message(
        user_id,
        "Вчера вы были у нас, спасибо!\nОцените пожалуйста от 1-5 нас!",
        parse_mode=None,
    )

    state = get_fsm(bot_id=bot.id, user_id=user_id, chat_id=user_id)
    await state.update_data(row=row)
    await state.set_state(UserStates.review)


async def start_scheduler() -> None:
    """Start scheduler for work with csv."""
    scheduler = AsyncIOScheduler()
    logging.getLogger("apscheduler").setLevel(level=logging.INFO)
    
    scheduler.add_job(
        check_csvs,
        "interval",
        timezone=ZoneInfo("Europe/Moscow"),
        minutes=5,
        max_instances=1,
    )
    scheduler.start()
