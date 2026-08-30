import base64

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from keyboards.product_list import ProductListCallback, keyboard_approve_products_builder
from keyboards.recipes_list import keyboard_recipes_builder, RecipesListCallback, keyboard_recipe_back_builder
from services import api_client
from states.recognize_states import RecognizeState

router = Router()


@router.message(F.photo)
async def get_recognize_photo_cmd(message: Message, state: FSMContext):
    photo = message.photo[-1]

    file_info = await message.bot.get_file(photo.file_id)

    file_bytes = await message.bot.download_file(file_info.file_path)
    image_b64 = base64.b64encode(file_bytes.read()).decode('utf-8')
    result = (await api_client.recognize(base64=image_b64)).get("products", [])

    if len(result) == 0:
        await message.reply("Не удалось распознать список продуктов. Попробуй еще раз")
        return

    await state.set_state(RecognizeState.waiting_for_product_list_approval)
    await state.update_data({"products": result})

    await message.reply(f"Мы распознали такие продукты. {', '.join(result)}\n"
                        f"Всё верно?", reply_markup=keyboard_approve_products_builder())


@router.message(F.document)
async def get_recognize_document_cmd(message: Message, state: FSMContext):
    document = message.document

    if document.mime_type != "image/":
        await message.reply("Я принимаю только текст/картинки")
        return

    file_info = await message.bot.get_file(document.file_id)

    file_bytes = await message.bot.download_file(file_info.file_path)
    image_b64 = base64.b64encode(file_bytes.read()).decode("utf-8")
    result = (await api_client.recognize(base64=image_b64)).get("products", [])

    if len(result) == 0:
        await message.reply("Не удалось распознать список продуктов. Попробуй еще раз")
        return

    await state.set_state(RecognizeState.waiting_for_product_list_approval)
    await state.update_data({"products": result})

    await message.reply(f"Мы распознали такие продукты. {', '.join(result)}\n"
                        f"Всё верно?", reply_markup=keyboard_approve_products_builder())


@router.message(F.text & ~F.text.startswith("/"))
async def get_recognize_text_cmd(message: Message, state: FSMContext):
    result = (await api_client.recognize(text=message.text)).get("products", [])

    if len(result) == 0:
        await message.reply("Не удалось распознать список продуктов. Попробуй еще раз")
        return

    await state.set_state(RecognizeState.waiting_for_product_list_approval)
    await state.update_data({"products": result})

    await message.reply(f"Мы распознали такие продукты. {', '.join(result)}\n"
                        f"Всё верно?", reply_markup=keyboard_approve_products_builder())


@router.callback_query(RecognizeState.waiting_for_product_list_approval, ProductListCallback.filter(F.approve == False))
async def get_not_approval_product_list(cb: CallbackQuery, callback_data: ProductListCallback, state: FSMContext):
    await state.set_state(None)
    await state.update_data({"products": None})

    await cb.message.answer(
        "К сожалению, распознать продукты у нас не получилось. Попробуйте еще раз отправить список продуктов/список продуктов")
    await cb.message.delete()


@router.callback_query(RecognizeState.waiting_for_product_list_approval, ProductListCallback.filter(F.approve))
async def get_approval_product_list(cb: CallbackQuery, callback_data: ProductListCallback, state: FSMContext):
    await cb.answer("Генерируем рецепты...")
    await state.set_state(RecognizeState.waiting_for_choose_recipe)
    products = await state.get_value("products", [])

    result = (await api_client.get_recipes(products)).get("recipes", [])
    await state.update_data({"recipes": result})

    recipes_for_kb = [(recipe.get("title"), i) for i, recipe in enumerate(result)]

    await cb.message.answer("Список рецептов: ", reply_markup=keyboard_recipes_builder(recipes_for_kb))
    await cb.message.delete()


@router.callback_query(RecognizeState.waiting_for_choose_recipe, RecipesListCallback.filter())
async def get_recipe_callback(cb: CallbackQuery, callback_data: RecipesListCallback, state: FSMContext):
    if callback_data.back:
        result = await state.get_value("recipes", [])
        recipes_for_kb = [(recipe.get("title"), i) for i, recipe in enumerate(result)]

        await cb.message.answer("Список рецептов: ", reply_markup=keyboard_recipes_builder(recipes_for_kb))
        await cb.message.delete()
        return

    recipe_num = callback_data.recipe_num
    recipes = await state.get_value("recipes")
    if not recipes or not isinstance(recipes, list) or len(recipes) == 0 or len(
            recipes[recipe_num].get("steps", [])) == 0:
        await cb.message.answer("Что-то пошло не так. Попробуйте еще раз")
        return

    text = ""
    for i, recipe in enumerate(recipes[recipe_num].get("steps", [])):
        text += f"Шаг {i + 1}. {recipe}\n"

    await cb.message.answer(text, reply_markup=keyboard_recipe_back_builder())
    await cb.message.delete()


@router.callback_query(ProductListCallback.filter())
async def reset_approval_product_list(cb: CallbackQuery, callback_data: ProductListCallback, state: FSMContext):
    await state.set_state(None)
    await state.update_data({"products": None})

    await cb.answer("Эта кнопка устарела")
    await cb.message.delete()
