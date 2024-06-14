import asyncio
from clinic_app.frontend.whatsapp_bot.constants import bot
from clinic_app.frontend.whatsapp_bot.handlers import middleware
from clinic_app.frontend.whatsapp_bot.scheduler import start_scheduler


async def main():
    await start_scheduler()
    bot.webhooks.startReceivingNotifications(middleware)


if __name__ == "__main__":
    asyncio.run(main())
