from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from aiogram.filters import Command

from services.api_client import withdraw_consent

router = Router()


@router.message(Command("delete"))
async def delete_cmd(message: Message, state: FSMContext):
    # Один вызов: журнал снимает все типы согласия; прокси удаляет telegram id.
    result = await withdraw_consent(external_id=str(message.from_user.id))
    if not result.get("ok"):
        await message.reply("Во время отзыва согласия что-то пошло не так. Попробуйте позже")
        return

    await state.clear()
    await message.reply(
        "Согласия отозваны. Чтобы снова воспользоваться ботом, введите /start")
