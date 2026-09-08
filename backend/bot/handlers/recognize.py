import base64
import json

import httpx
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from keyboards.product_list import ProductListCallback, keyboard_approve_products_builder
from keyboards.recipes_list import keyboard_recipes_builder, RecipesListCallback, keyboard_recipe_back_builder
from services import api_client
from states.recognize_states import RecognizeState

router = Router()


async def handle_recognize(message: Message, state: FSMContext, params: dict):
    user_id = message.from_user.id if message.from_user else None

    try:
        result = (await api_client.recognize(**params)).get("products", [])
    except httpx.HTTPError:
        await message.reply("Не удалось распознать список продуктов. Попробуй еще раз список/фото товаров")
        return
    except json.JSONDecodeError:
        await message.reply("Не удалось распознать список продуктов. Попробуй еще раз список/фото товаров")
        return

    if len(result) == 0:
        await message.reply("Не удалось распознать список продуктов. Попробуй еще раз список/фото товаров")
        return

    await state.set_state(RecognizeState.waiting_for_product_list_approval)
    await state.update_data({"products": result})

    await message.reply(f"Мы распознали такие продукты. {', '.join(result)}\n"
                        f"Всё верно?", reply_markup=keyboard_approve_products_builder())


@router.message(F.photo)
async def get_recognize_photo_cmd(message: Message, state: FSMContext):
    user_id = message.from_user.id if message.from_user else None
    photo = message.photo[-1]

    file_info = await message.bot.get_file(photo.file_id)

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

    file_bytes = await message.bot.download_file(file_info.file_path)
    image_b64 = base64.b64encode(file_bytes.read()).decode("utf-8")

    await handle_recognize(message, state, {"base64": image_b64})


@router.message(F.text & ~F.text.startswith("/"))
async def get_recognize_text_cmd(message: Message, state: FSMContext):
    user_id = message.from_user.id if message.from_user else None
    text_len = len(message.text) if message.text else 0
    await handle_recognize(message, state, {"text": message.text})


@router.callback_query(RecognizeState.waiting_for_product_list_approval, ProductListCallback.filter(F.approve == False))
async def get_not_approval_product_list(cb: CallbackQuery, callback_data: ProductListCallback, state: FSMContext):
    user_id = cb.from_user.id if cb.from_user else None
    await state.set_state(None)
    await state.update_data({"products": None})

    await cb.message.answer(
        "К сожалению, распознать продукты у нас не получилось. Попробуйте еще раз отправить список/фото продуктов")
    await cb.message.delete()


@router.callback_query(RecognizeState.waiting_for_product_list_approval, ProductListCallback.filter(F.approve))
async def get_approval_product_list(cb: CallbackQuery, callback_data: ProductListCallback, state: FSMContext):
    user_id = cb.from_user.id if cb.from_user else None
    await cb.answer("Генерируем рецепты...")
    await state.set_state(RecognizeState.waiting_for_choose_recipe)
    products = await state.get_value("products", [])

    try:
        result = (await api_client.get_recipes(products)).get("recipes", [])
    except httpx.HTTPError:
        await cb.message.reply("Не удалось сгенерировать список рецептов. Попробуйте еще раз отправить список/фото продуктов")
    except httpx.HTTPError as exc:
        await cb.message.reply(
            "Не удалось сгенерировать список рецептов. Попробуйте еще раз отправить список/фото продуктов")
        return
    except json.JSONDecodeError:
        await cb.message.reply("Не удалось сгенерировать список рецептов. Попробуйте еще раз отправить список/фото продуктов")
    except json.JSONDecodeError as exc:
        await cb.message.reply(
            "Не удалось сгенерировать список рецептов. Попробуйте еще раз отправить список/фото продуктов")
        return

    await state.update_data({"recipes": result})

    recipes_for_kb = [(recipe.get("title"), i) for i, recipe in enumerate(result)]

    await cb.message.answer("Список рецептов: ", reply_markup=keyboard_recipes_builder(recipes_for_kb))
    await cb.message.delete()


@router.callback_query(RecognizeState.waiting_for_choose_recipe, RecipesListCallback.filter())
async def get_recipe_callback(cb: CallbackQuery, callback_data: RecipesListCallback, state: FSMContext):
    user_id = cb.from_user.id if cb.from_user else None

    if callback_data.back:
        result = await state.get_value("recipes", [])
        recipes_for_kb = [(recipe.get("title"), i) for i, recipe in enumerate(result)]

        await cb.message.answer("Список рецептов: ", reply_markup=keyboard_recipes_builder(recipes_for_kb))
        await cb.message.delete()
        return

    recipe_num = callback_data.recipe_num
    recipes = await state.get_value("recipes", [])
    if not recipes or len(recipes) == 0 or recipe_num >= len(recipes) or len(
            recipes[recipe_num].get("steps", [])) == 0:
        await cb.message.answer("Что-то пошло не так. Попробуйте еще раз выбрать рецепт, либо отправить список/фото товаров")
        return

    text = ""
    for i, recipe in enumerate(recipes[recipe_num].get("steps", [])):
        text += f"Шаг {i + 1}. {recipe}\n"
    text = '\n'.join(f"Шаг {i + 1}. {recipe}" for i, recipe in enumerate(recipes[recipe_num].get("steps", [])))

    await cb.message.answer(text, reply_markup=keyboard_recipe_back_builder())
    await cb.message.delete()


@router.callback_query(ProductListCallback.filter())
async def reset_approval_product_list(cb: CallbackQuery, callback_data: ProductListCallback, state: FSMContext):
    user_id = cb.from_user.id if cb.from_user else None
    await state.set_state(None)
    await state.update_data({"products": None})

    await cb.answer("Эта кнопка устарела")
    await cb.message.delete()
