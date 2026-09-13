import base64
import json
import logging

import httpx
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from keyboards.product_list import ProductListCallback, keyboard_approve_products_builder
from keyboards.recipes_list import keyboard_recipes_builder, RecipesListCallback, keyboard_recipe_back_builder
from services import api_client
from states.recognize_states import RecognizeState

router = Router()
logger = logging.getLogger(__name__)


async def handle_recognize(message: Message, state: FSMContext, params: dict):
    user_id = message.from_user.id if message.from_user else None

    answer_message = await message.reply("В обработке...")

    try:
        result = (await api_client.recognize(**params)).get("products", [])
    except httpx.HTTPError as exc:
        logger.warning("handle_recognize: user_id=%s recognize HTTP error: %s", user_id, exc)
        await answer_message.edit_text(
            "Не удалось распознать список продуктов. Попробуй еще раз отправить список/фото продуктов")
        return
    except json.JSONDecodeError as exc:
        logger.warning("handle_recognize: user_id=%s recognize JSON decode error: %s", user_id, exc)
        await answer_message.edit_text(
            "Не удалось распознать список продуктов. Попробуй еще раз отправить список/фото продуктов")
        return

    if len(result) == 0:
        logger.warning("handle_recognize: user_id=%s no products recognized", user_id)
        await answer_message.edit_text(
            "Не удалось распознать список продуктов. Попробуй еще раз отправить список/фото продуктов")
        return

    if not all(isinstance(r, str) for r in result):
        logger.warning("handle_recognize: user_id=%s invalid products structure: %r", user_id, result)
        await answer_message.edit_text(
            "Не удалось распознать список продуктов. Попробуй еще раз отправить список/фото продуктов")
        return

    logger.info("handle_recognize: user_id=%s products recognized, count=%d", user_id, len(result))

    await state.set_state(RecognizeState.waiting_for_product_list_approval)
    await state.update_data({"products": result})

    await answer_message.edit_text(f"Мы распознали такие продукты. {', '.join(result)}\n"
                                   f"Всё верно?", reply_markup=keyboard_approve_products_builder())


@router.message(F.photo)
async def get_recognize_photo_cmd(message: Message, state: FSMContext):
    user_id = message.from_user.id if message.from_user else None
    photo = message.photo[-1]

    file_info = await message.bot.get_file(photo.file_id)
    logger.info("get_recognize_photo: user_id=%s file_id=%s", user_id, photo.file_id)

    file_bytes = await message.bot.download_file(file_info.file_path)
    image_b64 = base64.b64encode(file_bytes.read()).decode('utf-8')

    await handle_recognize(message, state, {"base64": image_b64})


@router.message(F.document)
async def get_recognize_document_cmd(message: Message, state: FSMContext):
    user_id = message.from_user.id if message.from_user else None
    document = message.document

    if not document.mime_type.startswith("image/"):
        logger.info("get_recognize_document: user_id=%s unsupported mime_type=%s", user_id, document.mime_type)
        await message.reply("Я принимаю только текст/картинки")
        return

    file_info = await message.bot.get_file(document.file_id)
    logger.info("get_recognize_document: user_id=%s file_id=%s", user_id, document.file_id)

    file_bytes = await message.bot.download_file(file_info.file_path)
    image_b64 = base64.b64encode(file_bytes.read()).decode("utf-8")

    await handle_recognize(message, state, {"base64": image_b64})


@router.message(F.text & ~F.text.startswith("/"))
async def get_recognize_text_cmd(message: Message, state: FSMContext):
    user_id = message.from_user.id if message.from_user else None
    text_len = len(message.text) if message.text else 0
    logger.info("get_recognize_text: user_id=%s text_len=%d", user_id, text_len)
    await handle_recognize(message, state, {"text": message.text})


@router.callback_query(RecognizeState.waiting_for_product_list_approval, ProductListCallback.filter(F.approve == False))
async def get_not_approval_product_list(cb: CallbackQuery, callback_data: ProductListCallback, state: FSMContext):
    user_id = cb.from_user.id if cb.from_user else None
    logger.info("get_not_approval_product_list: user_id=%s products not approved", user_id)
    await state.set_state(None)
    await state.update_data({"products": None})

    await cb.message.edit_text(
        "К сожалению, распознать продукты у нас не получилось. Попробуйте еще раз отправить список/фото продуктов")


@router.callback_query(RecognizeState.waiting_for_product_list_approval, ProductListCallback.filter(F.approve))
async def get_approval_product_list(cb: CallbackQuery, callback_data: ProductListCallback, state: FSMContext):
    user_id = cb.from_user.id if cb.from_user else None
    await cb.message.edit_text("Генерируем рецепты...", reply_markup=None)
    await state.set_state(RecognizeState.waiting_for_choose_recipe)
    products = await state.get_value("products", [])
    logger.info("get_approval_product_list: user_id=%s generating recipes for %d products", user_id, len(products))

    try:
        result = (await api_client.get_recipes(products)).get("recipes", [])
    except httpx.HTTPError as exc:
        logger.warning("get_approval_product_list: user_id=%s recipes HTTP error: %s", user_id, exc)
        await cb.message.reply(
            "Не удалось сгенерировать список рецептов. Попробуйте еще раз отправить список/фото продуктов")
        return
    except json.JSONDecodeError as exc:
        logger.warning("get_approval_product_list: user_id=%s recipes JSON decode error: %s", user_id, exc)
        await cb.message.reply(
            "Не удалось сгенерировать список рецептов. Попробуйте еще раз отправить список/фото продуктов")
        return

    logger.info("get_approval_product_list: user_id=%s recipes generated, count=%d", user_id, len(result))
    await state.update_data({"recipes": result})

    recipes_for_kb = [(recipe.get("title"), i) for i, recipe in enumerate(result)]

    await cb.message.edit_text("Список рецептов: ", reply_markup=keyboard_recipes_builder(recipes_for_kb))


@router.callback_query(RecognizeState.waiting_for_choose_recipe, RecipesListCallback.filter())
async def get_recipe_callback(cb: CallbackQuery, callback_data: RecipesListCallback, state: FSMContext):
    user_id = cb.from_user.id if cb.from_user else None

    if callback_data.back:
        result = await state.get_value("recipes", [])
        recipes_for_kb = [(recipe.get("title"), i) for i, recipe in enumerate(result)]
        logger.info("get_recipe_callback: user_id=%s back to recipes list", user_id)

        await cb.message.edit_text("Список рецептов: ", reply_markup=keyboard_recipes_builder(recipes_for_kb))
        return

    recipe_num = callback_data.recipe_num
    recipes = await state.get_value("recipes", [])
    if not recipes or len(recipes) == 0 or recipe_num >= len(recipes) or len(
            recipes[recipe_num].get("steps", [])) == 0:
        logger.warning("get_recipe_callback: user_id=%s invalid recipe selection num=%d total=%d",
                       user_id, recipe_num, len(recipes))
        await cb.message.answer(
            "Что-то пошло не так. Попробуйте еще раз выбрать рецепт, либо отправить список/фото продуктов")
        return

    text = recipes[recipe_num].get("title", "Тут должно быть название рецепта") + "\n\n"
    text += '\n'.join(f"Шаг {i + 1}. {recipe}" for i, recipe in enumerate(recipes[recipe_num].get("steps", [])))
    logger.info("get_recipe_callback: user_id=%s opened recipe num=%d", user_id, recipe_num)

    await cb.message.edit_text(text, reply_markup=keyboard_recipe_back_builder())


@router.callback_query(ProductListCallback.filter())
async def reset_approval_product_list(cb: CallbackQuery, callback_data: ProductListCallback, state: FSMContext):
    user_id = cb.from_user.id if cb.from_user else None
    logger.info("reset_approval_product_list: user_id=%s stale approval button pressed", user_id)
    await state.set_state(None)
    await state.update_data({"products": None})

    await cb.answer("Эта кнопка устарела")
    await cb.message.delete()
