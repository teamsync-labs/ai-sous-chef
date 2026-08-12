import base64

from aiogram import Router, F
from aiogram.types import Message
from services import api_client

router = Router()


@router.message(F.photo)
async def get_recognize_photo_cmd(message: Message):
    photo = message.photo[-1]

    file_info = await message.bot.get_file(photo.file_id)

    file_bytes = await message.bot.download_file(file_info.file_path)
    image_b64 = base64.b64encode(file_bytes.read()).decode('utf-8')
    result = await api_client.recognize(base64=image_b64)
    await message.reply(f"Было отправлено фото. Результат {result}")


@router.message(F.document)
async def get_recognize_photo_cmd(message: Message):
    document = message.document

    file_info = await message.bot.get_file(document.file_id)

    file_bytes = await message.bot.download_file(file_info.file_path)
    image_b64 = base64.b64encode(file_bytes.read()).decode("utf-8")
    result = await api_client.recognize(base64=image_b64)
    await message.reply(f"Был отправлен файл (фото). Результат: {result}")


@router.message(F.text)
async def get_recognize_text_cmd(message: Message):
    result = await api_client.recognize(text=message.text)
    await message.reply(f"Был отправлен текст. Результат {result}")
