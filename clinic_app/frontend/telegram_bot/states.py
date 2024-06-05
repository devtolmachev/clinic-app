from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.base import StorageKey
from clinic_app.frontend.telegram_bot.contants import storage


class UserStates(StatesGroup):
    """User states."""

    get_phone = State()
    notify_tommorow = State()
    review = State()
    rescheduling = State()
    get_review = State()


def get_fsm(bot_id: int, user_id: int, chat_id: int) -> FSMContext:
    """Get aiogram bot FSMContext from dialog."""
    return FSMContext(
        storage=storage,
        key=StorageKey(
            bot_id=bot_id,
            user_id=user_id,
            chat_id=chat_id,
        ),
    )
