import asyncio

from clinic_app.frontend.whatsapp_bot.constants import bot
from clinic_app.frontend.whatsapp_bot.handlers import run_work
from clinic_app.frontend.whatsapp_bot.scheduler import start_scheduler


async def prepare_bot():
    set_settings_body = {
        "webhookUrl": "",
        "outgoingWebhook": "yes",
        "stateWebhook": "yes",
        "incomingWebhook": "yes",
    }

    get_settings = bot.api.account.getSettings
    settings = await asyncio.to_thread(get_settings)
    for k, v in settings.data.items():
        if k in set_settings_body and v != set_settings_body[k]:
            await asyncio.to_thread(
                bot.api.account.setSettings, set_settings_body
            )
            return


async def keep_alive():
    while True:
        await asyncio.sleep(3600)


async def main():
    await prepare_bot()

    await start_scheduler()
    bot.run_forever()
    run_work()


if __name__ == "__main__":
    asyncio.run(main())
