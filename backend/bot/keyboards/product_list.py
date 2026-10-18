from enum import Enum
from aiogram.filters.callback_data import CallbackData

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class ProductListAction(str, Enum):
    APPROVE = "approve"
    EDIT = "edit"
    REJECT = "reject"


class ProductListCallback(CallbackData, prefix="product_list"):
    action: ProductListAction


def keyboard_approve_products_builder() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Верно", callback_data=ProductListCallback(action=ProductListAction.APPROVE))
    kb.button(text="Редактировать", callback_data=ProductListCallback(action=ProductListAction.EDIT))
    kb.button(text="Всё неверно", callback_data=ProductListCallback(action=ProductListAction.REJECT))
    kb.adjust(1)
    return kb.as_markup()
