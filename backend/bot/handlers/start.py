from aiogram import Router
from aiogram.types import Message

from aiogram.filters import CommandStart

router = Router()


@router.message(CommandStart())
async def start_cmd(message: Message):
    await message.reply("Была использована команда /start")
