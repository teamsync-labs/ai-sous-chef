from enum import Enum
from aiogram.filters.callback_data import CallbackData

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class ProductListAction(str, Enum):
    APPROVE = "approve"
    EDIT = "edit"
    REJECT = "reject"


class EditProductListAction(str, Enum):
    SELECT = "select"
    PREV = "prev"
    NEXT = "next"
    FINISH = "finish"


class ProductListCallback(CallbackData, prefix="product_list"):
    action: ProductListAction


class EditProductListPagination(CallbackData, prefix="edit_product_pag"):
    action: EditProductListAction = EditProductListAction.SELECT
    page: int = 0
    index: int = -1


def keyboard_approve_products_builder() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Верно", callback_data=ProductListCallback(action=ProductListAction.APPROVE))
    kb.button(text="Редактировать", callback_data=ProductListCallback(action=ProductListAction.EDIT))
    kb.button(text="Всё неверно", callback_data=ProductListCallback(action=ProductListAction.REJECT))
    kb.adjust(1)
    return kb.as_markup()


def keyboard_edit_products_builder(products: list[str], page: int = 0, per_page: int = 7) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    total = len(products)
    last_page = max(0, (total - 1) // per_page)
    page = min(max(page, 0), last_page)

    start = page * per_page
    end = min(start + per_page, total)

    for i in range(start, end):
        kb.row(InlineKeyboardButton(
            text=products[i],
            callback_data=EditProductListPagination(
                index=i, page=page).pack()))
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=EditProductListPagination(
                    action=EditProductListAction.PREV, page=page - 1).pack()
            )
        )
    if page < last_page:
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=EditProductListPagination(
                    action=EditProductListAction.NEXT, page=page + 1).pack()
            )
        )

    if nav_buttons:
        kb.row(*nav_buttons, width=2)

    kb.row(InlineKeyboardButton(
        text="Завершить",
        callback_data=EditProductListPagination(
            action=EditProductListAction.FINISH, page=page).pack()))

    return kb.as_markup()
