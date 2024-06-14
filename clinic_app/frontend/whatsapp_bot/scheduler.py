from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import numpy as np
from clinic_app.backend.csv_files import CSVFile, Database
from clinic_app.backend.utils import format_phone
from clinic_app.frontend.whatsapp_bot.constants import bot
from clinic_app.frontend.whatsapp_bot.states import get_fsm, MainFSM
from clinic_app.shared import CSVS
from zoneinfo import ZoneInfo

if TYPE_CHECKING:
    from pandas import Series


def get_user_id(row: Series) -> int | None:
    """Get user id from database csv file by phone."""
    db = Database()
    phone = format_phone(row["Телефон"])
    return db.get_value_by_kv(("phone", phone), "wh_user_id")


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
    if not user_id or np.isnan(user_id):
        return

    bot.sending.sendMessage(
        user_id,
        f"Вы записались на {row["ДатаНачала"]}, подтверждаете запись?",
    )

    state = get_fsm()
    state.set_state(MainFSM.notify_tommorow, user_id)
    state.update_data(user_id, info_data=row, csv=csv)


async def notify_before_2hours(row: Series, csv: CSVFile) -> None:
    """Notify before 2 hours work.

    Interact with `2hours.csv` file
    """
    user_id = get_user_id(row=row)
    if not user_id or np.isnan(user_id):
        return

    bot.sending.sendMessage(
        user_id,
        "Ждем вас сегодня в время по адресу! Будем рады вас видеть"
    )


async def notify_review(row: Series, csv: CSVFile) -> None:
    """Notify add review work.

    Interact with `Reviews.csv` file
    """
    user_id = get_user_id(row=row)
    if not user_id or np.isnan(user_id):
        return

    bot.sending.sendMessage(
        user_id,
        "Вчера вы были у нас, спасибо!\nОцените пожалуйста от 1-5 нас!",
    )
    
    state = get_fsm()
    state.set_state(MainFSM.review, user_id)
    state.update_data(user_id, row=row)


async def start_scheduler() -> None:
    """Start scheduler for work with csv."""
    await check_csvs()
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        check_csvs,
        "interval",
        timezone=ZoneInfo("Europe/Moscow"),
        minutes=5,
        max_instances=1,
    )
    scheduler.start()
