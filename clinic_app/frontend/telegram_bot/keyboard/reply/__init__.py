"""Contains reply keyboard for telegram bot."""

from __future__ import annotations

from typing import Any

from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def _build_btns(btns_data: list[dict[str, Any]]) -> ReplyKeyboardBuilder:
    """Return `ReplyKeyboardBuilder` with buttons with btn data."""
    kb = ReplyKeyboardBuilder()

    for btn_data in btns_data:
        kb.add(KeyboardButton(**btn_data))

    return kb

def yes_no(adjust: int | tuple[int] = 2) -> ReplyKeyboardBuilder:
    """Get keyboard with yes and no buttons."""
    btns_data = [
        {"text": "Да"},
        {"text": "Нет"},
    ]

    kb = _build_btns(btns_data)
    kb.adjust(adjust)
    return kb
