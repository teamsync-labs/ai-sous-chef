from aiogram.filters.callback_data import CallbackData

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class ConsentCallback(CallbackData, prefix="consent"):
    question: int
    consent: bool


def keyboard_consent_builder(params: tuple[str, str], question_num=1) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=params[0], url=params[1])
    kb.button(text="Согласен", callback_data=ConsentCallback(question=question_num, consent=True))
    kb.button(text="Не согласен", callback_data=ConsentCallback(question=question_num, consent=False))
    kb.adjust(1)
    return kb.as_markup()
