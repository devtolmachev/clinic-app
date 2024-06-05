import logging

from clinic_app.frontend.telegram_bot.contants import bot, dp
from clinic_app.frontend.telegram_bot.handlers import register_handlers
from clinic_app.frontend.telegram_bot.scheduler import start_scheduler


async def main() -> None:
    """Entrypoint in telegram bot."""
    await start_scheduler()
    register_handlers()

    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
