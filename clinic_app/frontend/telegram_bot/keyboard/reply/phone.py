from __future__ import annotations

from typing import TYPE_CHECKING

from ..reply import _build_btns  # noqa: TID252

if TYPE_CHECKING:
    from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_phone_markup(
    adjust: int | tuple[int] = 3, btn_text: str = "Отправить номер телефона"
) -> ReplyKeyboardBuilder:
    """Get button with phone request.

    Parameters
    ----------
    adjust : int, optional
        this parameter will pass to `kb.adjust`, by default 3.
    btn_text : str, optional
        button text, by default "Отправить номер телефона".

    Returns
    -------
    ReplyKeyboardBuilder
        reply keyboard builder.
    """
    btns_data = [{"text": btn_text, "request_contact": True}]

    kb = _build_btns(btns_data)
    kb.adjust(adjust)
    return kb
