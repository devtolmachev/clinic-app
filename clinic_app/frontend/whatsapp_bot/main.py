import asyncio

from clinic_app.frontend.whatsapp_bot.constants import bot
from clinic_app.frontend.whatsapp_bot.handlers import middleware
from clinic_app.frontend.whatsapp_bot.scheduler import start_scheduler
from clinic_app.shared.config import get_config


async def prepare_bot():
    set_settings_body = {
        # "webhookUrl": get_config()["whatsapp_bot"]["webhook_url"],
        "webhookUrl": "",
        "outgoingWebhook": "yes",
        "stateWebhook": "yes",
        "incomingWebhook": "yes",
    }

    get_settings = bot.account.getSettings
    settings = await asyncio.to_thread(get_settings)
    for k, v in settings.data.items():
        if k in set_settings_body and v != set_settings_body[k]:
            await asyncio.to_thread(bot.account.setSettings, set_settings_body)
            return


async def keep_alive():
    while True:
        await asyncio.sleep(3600)


async def main():
    await prepare_bot()

    await start_scheduler()
    bot.webhooks.startReceivingNotifications(middleware)


if __name__ == "__main__":
    asyncio.run(main())
