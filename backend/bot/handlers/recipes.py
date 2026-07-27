from aiogram import Router, F
from aiogram.types import Message

router = Router()


@router.message(F.text)
async def get_recipes_cmd(message: Message):
    await message.reply(f"Был отправлен текст: {message.text}")
