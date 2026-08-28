from aiogram.filters.callback_data import CallbackData

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class RecipesListCallback(CallbackData, prefix="recipes_list"):
    recipe_num: int = 0
    back: bool = False


def keyboard_recipes_builder(recipes: list[tuple[str, int]]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for recipe_name, recipe_num in recipes:
        kb.button(text=recipe_name, callback_data=RecipesListCallback(recipe_num=recipe_num))
    kb.adjust(1)
    return kb.as_markup()


def keyboard_recipe_back_builder() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="К списку рецептов", callback_data=RecipesListCallback(back=True))
    kb.adjust(1)
    return kb.as_markup()
