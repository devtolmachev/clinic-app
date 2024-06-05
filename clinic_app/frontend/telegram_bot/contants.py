from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from clinic_app.shared.config import get_config

cfg = get_config()
bot = Bot(
    token=cfg["telegram_bot"]["token"],
    default=DefaultBotProperties(parse_mode="MarkdownV2"),
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
