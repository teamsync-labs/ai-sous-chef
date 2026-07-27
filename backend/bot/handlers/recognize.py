from aiogram import Router, F
from aiogram.types import Message

router = Router()


@router.message(F.photo)
async def get_recognize_cmd(message: Message):
    await message.reply("Было отправлено фото")
