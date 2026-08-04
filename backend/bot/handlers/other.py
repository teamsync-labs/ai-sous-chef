from aiogram import Router
from aiogram.types import Message

router = Router()


@router.message()
async def any_msg(message: Message):
    await message.reply("Неизвестное сообщение")
