import os
import logging
import asyncio

from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()

from middlewares.ConsentMiddlwares import ConsentMiddleware

from aiogram import Dispatcher, Bot

from aiogram.client.session.aiohttp import AiohttpSession

from handlers import routers

from utils.logging import setup_logging

setup_logging()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)
dp.message.middleware(ConsentMiddleware())
# dp.callback_query.middleware(ConsentMiddleware())


async def main():
    logger.info("Запускается")
    token = os.getenv("TG_TOKEN")
    if not token:
        raise ValueError("TG_TOKEN не найден в переменных окружения")
    proxy_url = os.getenv("TG_PROXY_URL")
    session = None
    if proxy_url:
        logger.info("Прокси для Telegram API задан")
        session = AiohttpSession(proxy=proxy_url)
    else:
        logger.info("TG_PROXY_URL не указан. Запуск без прокси")

    dp.include_routers(*routers)
    bot = Bot(token=token, session=session)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
