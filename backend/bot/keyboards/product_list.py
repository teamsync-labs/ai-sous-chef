from aiogram.filters.callback_data import CallbackData

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class ProductListCallback(CallbackData, prefix="product_list"):
    approve: bool


def keyboard_approve_products_builder() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Верно", callback_data=ProductListCallback(approve=True))
    kb.button(text="Неверно", callback_data=ProductListCallback(approve=False))
    kb.adjust(1)
    return kb.as_markup()
