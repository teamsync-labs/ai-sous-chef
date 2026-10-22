import base64
import json
import logging

import httpx
from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from keyboards.product_list import ProductListCallback, keyboard_approve_products_builder, ProductListAction, \
    keyboard_edit_products_builder, EditProductListPagination, EditProductListAction
from keyboards.recipes_list import keyboard_recipes_builder, RecipesListCallback, keyboard_recipe_back_builder
from services import api_client
from states.recognize_states import RecognizeState

router = Router()
logger = logging.getLogger(__name__)

ERROR_RECOGNIZE = "Не удалось распознать список продуктов. Попробуй еще раз отправить список/фото продуктов"
ERROR_RECIPES = "Не удалось сгенерировать список рецептов. Попробуйте еще раз отправить список/фото продуктов"
CHOOSE_PRODUCT = "Выберите продукты для удаления, либо напишите, какие продукты добавить"

def _recipes_for_kb(recipes):
    return [(r.get("title"), i) for i, r in enumerate(recipes)]

def answer_callback_once(func):
    async def wrapper(cb, *args, **kwargs):
        result = await func(cb, *args, **kwargs)
        if not cb.answered:
            await cb.answer()
        return result

    return wrapper


async def handle_recognize(message: Message, state: FSMContext, params: dict):
    user_id = message.from_user.id

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
        await answer_message.edit_text(ERROR_RECOGNIZE)
        return

    if not all(isinstance(r, str) for r in result):
        logger.warning("handle_recognize: user_id=%s invalid products structure: %r", user_id, result)
        await answer_message.edit_text(ERROR_RECOGNIZE)
        return

    logger.info("handle_recognize: user_id=%s products recognized, count=%d", user_id, len(result))

    await state.set_state(RecognizeState.waiting_for_product_list_approval)
    await state.update_data({"products": result})

    await answer_message.edit_text(f"Мы распознали такие продукты. {', '.join(result)}\n"
                                   f"Всё верно?", reply_markup=keyboard_approve_products_builder())


async def download_file_as_base64(bot: Bot, file_id: str) -> str:
    file_info = await bot.get_file(file_id)
    file_bytes = await bot.download_file(file_info.file_path)
    if file_bytes is None:
        raise RuntimeError(f"Failed to downlload file {file_id}")
    file_bytes.seek(0)
    return base64.b64encode(file_bytes.read()).decode('utf-8')


@router.message(RecognizeState.waiting_for_editing_product_list, F.text)
async def get_new_product(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    msg_id = await state.get_value("editing_message_id")
    if not msg_id:
        logger.warning("get_new_product: user_id=%s editing_message_id is missing", user_id)
        await msg.answer("Ошибка. Продукт не был добавлен. Попробуйте еще раз")
        return

    product = msg.text.strip()
    if not product:
        logger.warning("get_new_product: user_id=%s empty product text", user_id)
        await msg.answer("Ошибка. Продукт не был добавлен. Попробуйте еще раз")
        return

    products = (await state.get_value("products", [])) + [product]
    await state.update_data({"products": products})
    await msg.bot.edit_message_text(
        message_id=msg_id,
        chat_id=msg.chat.id,
        text=CHOOSE_PRODUCT,
        reply_markup=keyboard_edit_products_builder(products))
    logger.info("get_new_product: user_id=%s editing %d products (added '%s')", user_id, len(products), product)


@router.message(F.photo)
async def get_recognize_photo_cmd(message: Message, state: FSMContext):
    user_id = message.from_user.id
    photo = message.photo[-1]

    image_b64 = await download_file_as_base64(message.bot, photo.file_id)

    logger.info("get_recognize_photo: user_id=%s file_id=%s", user_id, photo.file_id)

    await handle_recognize(message, state, {"base64": image_b64})


@router.message(F.document)
async def get_recognize_document_cmd(message: Message, state: FSMContext):
    user_id = message.from_user.id
    document = message.document

    if document.mime_type is None or not document.mime_type.startswith("image/"):
        logger.info("get_recognize_document: user_id=%s unsupported mime_type=%s", user_id, document.mime_type)
        await message.reply("Я принимаю только текст/картинки")
        return

    image_b64 = await download_file_as_base64(message.bot, document.file_id)

    logger.info("get_recognize_document: user_id=%s file_id=%s", user_id, document.file_id)

    await handle_recognize(message, state, {"base64": image_b64})


@router.message(F.text & ~F.text.startswith("/"))
async def get_recognize_text_cmd(message: Message, state: FSMContext):
    if not message.text or not message.text.strip():
        await message.answer(ERROR_RECOGNIZE)
        return
    user_id = message.from_user.id
    logger.info("get_recognize_text: user_id=%s text_len=%d",
                user_id, len(message.text) if message.text else 0)
    await handle_recognize(message, state, {"text": message.text})


@answer_callback_once
@router.callback_query(RecognizeState.waiting_for_product_list_approval,
                       ProductListCallback.filter(F.action == ProductListAction.REJECT))
async def get_not_approval_product_list(cb: CallbackQuery, callback_data: ProductListCallback, state: FSMContext):
    user_id = cb.from_user.id
    logger.info("get_not_approval_product_list: user_id=%s rejected products, state reset", user_id)
    await state.set_state(None)
    await state.update_data({"products": None})

    await cb.message.edit_text(ERROR_RECOGNIZE)


@answer_callback_once
@router.callback_query(RecognizeState.waiting_for_product_list_approval,
                       ProductListCallback.filter(F.action == ProductListAction.EDIT))
async def get_editing_product_list(cb: CallbackQuery, callback_data: ProductListCallback, state: FSMContext):
    user_id = cb.from_user.id
    products = await state.get_value("products", [])
    msg = await cb.message.edit_text(CHOOSE_PRODUCT,
                                     reply_markup=keyboard_edit_products_builder(products))
    await state.update_data({"editing_message_id": msg.message_id})
    await state.set_state(RecognizeState.waiting_for_editing_product_list)
    logger.info("get_editing_product_list: user_id=%s editing %d products", user_id, len(products))


@answer_callback_once
@router.callback_query(RecognizeState.waiting_for_editing_product_list,
                       EditProductListPagination.filter(
                           F.action.in_([EditProductListAction.PREV, EditProductListAction.NEXT])))
async def get_pagination_product_list(cb: CallbackQuery, callback_data: EditProductListPagination, state: FSMContext):
    user_id = cb.from_user.id
    products = await state.get_value("products", [])
    await cb.message.edit_text(CHOOSE_PRODUCT,
                               reply_markup=keyboard_edit_products_builder(products, page=callback_data.page))
    logger.info("get_pagination_product_list: user_id=%s editing %d products", user_id, len(products))


@answer_callback_once
@router.callback_query(RecognizeState.waiting_for_editing_product_list,
                       EditProductListPagination.filter(F.action == EditProductListAction.SELECT))
async def get_remove_product_from_list(cb: CallbackQuery, callback_data: EditProductListPagination, state: FSMContext):
    user_id = cb.from_user.id
    products: list = await state.get_value("products", [])
    if len(products) == 0:
        logger.info("get_remove_product_from_list: user_id=%s product list emptied", user_id)

    if not (0 <= callback_data.index < len(products)):
        logger.warning("get_remove_product_from_list: user_id=%s index=%d out of range for %d products", user_id,
                       callback_data.index, len(products))
        await cb.message.edit_text(
            "Что-то пошло не так, попробуйте еще раз, либо завершите работу с редактированием списка товаров")
        return

    products = products.copy()
    del products[callback_data.index]
    if len(products) == 0:
        await cb.message.edit_text(
            "Список продуктов пуст. Напишите новый продукт текстом или завершите редактирование.",
            reply_markup=keyboard_edit_products_builder(products, page=0)
        )
        return

    await state.update_data({"products": products})
    await cb.message.edit_text(CHOOSE_PRODUCT,
                               reply_markup=keyboard_edit_products_builder(products, page=callback_data.page))
    logger.info("get_remove_product_from_list: user_id=%s editing %d products", user_id, len(products))


@answer_callback_once
@router.callback_query(RecognizeState.waiting_for_editing_product_list,
                       EditProductListPagination.filter(F.action == EditProductListAction.FINISH))
@router.callback_query(RecognizeState.waiting_for_product_list_approval,
                       ProductListCallback.filter(F.action == ProductListAction.APPROVE))
async def get_approval_product_list(cb: CallbackQuery, callback_data: ProductListCallback | EditProductListPagination,
                                    state: FSMContext):
    user_id = cb.from_user.id
    await cb.message.edit_text("Генерируем рецепты...", reply_markup=None)
    await state.set_state(RecognizeState.waiting_for_choose_recipe)
    products = await state.get_value("products", [])
    logger.info("get_approval_product_list: user_id=%s generating recipes for %d products from %s state", user_id,
                len(products), (await state.get_state()))

    try:
        result = (await api_client.get_recipes(products)).get("recipes", [])
    except httpx.HTTPError as exc:
        logger.warning("get_approval_product_list: user_id=%s recipes HTTP error: %s", user_id, exc)
        await cb.message.reply(ERROR_RECIPES)
        return
    except json.JSONDecodeError as exc:
        logger.warning("get_approval_product_list: user_id=%s recipes JSON decode error: %s", user_id, exc)
        await cb.message.reply(ERROR_RECIPES)
        return
    except Exception as exc:
        logger.warning("get_approval_product_list: user_id=%s recipes error: %s", user_id, exc, exc_info=True)
        await cb.message.reply(ERROR_RECIPES)
        return

    logger.info("get_approval_product_list: user_id=%s recipes generated, count=%d", user_id, len(result))
    await state.update_data({"recipes": result})

    await cb.message.edit_text("Список рецептов: ",
                               reply_markup=keyboard_recipes_builder(_recipes_for_kb(result)))


@answer_callback_once
@router.callback_query(RecognizeState.waiting_for_choose_recipe, RecipesListCallback.filter())
async def get_recipe_callback(cb: CallbackQuery, callback_data: RecipesListCallback, state: FSMContext):
    user_id = cb.from_user.id

    if callback_data.back:
        result = await state.get_value("recipes", [])
        logger.info("get_recipe_callback: user_id=%s back to recipes list", user_id)

        await cb.message.edit_text("Список рецептов: ", reply_markup=keyboard_recipes_builder(_recipes_for_kb(result)))
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
    user_id = cb.from_user.id
    logger.info("reset_approval_product_list: user_id=%s stale approval button pressed", user_id)
    await state.set_state(None)
    await state.update_data({"products": [],
                             "recipes": [],
                             "editing_message_id": None})

    await cb.answer(text="Эта кнопка устарела")
    await cb.message.delete()
