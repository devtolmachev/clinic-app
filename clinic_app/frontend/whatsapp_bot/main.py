import asyncio

from clinic_app.frontend.whatsapp_bot.constants import bot
from clinic_app.frontend.whatsapp_bot.handlers import error_handler, middleware
from clinic_app.frontend.whatsapp_bot.scheduler import start_scheduler


@error_handler
async def keep_alive():
    while True:
        notification = await asyncio.to_thread(
            bot.webhooks.api.receiving.receiveNotification
        )
        if (
            notification.data
            and notification.data["body"]["typeWebhook"]
            == "incomingMessageReceived"
        ):
            notification_id = notification.data["receiptId"]
            
            type_webhook = notification.data["body"]["typeWebhook"]
            body = notification.data["body"]
            middleware(type_webhook, body)
            
            await asyncio.to_thread(
                bot.webhooks.api.receiving.deleteNotification, notification_id
            )


async def prepare_bot():
    set_settings_body = {
        "webhookUrl": "",
        "outgoingWebhook": "yes",
        "stateWebhook": "yes",
        "incomingWebhook": "yes",
    }

    # get_settings = bot.account.getSettings
    # settings = await asyncio.to_thread(get_settings)
    # if settings != set_settings_body:
    await asyncio.to_thread(bot.account.setSettings, set_settings_body)


async def main():
    await start_scheduler()

    await prepare_bot()
    await keep_alive()

    # bot.webhooks.startReceivingNotifications(middleware)


if __name__ == "__main__":
    asyncio.run(main())
