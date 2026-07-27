import os
import logging
import asyncio

from dotenv import load_dotenv

from aiogram import Dispatcher, Bot

from aiogram.client.session.aiohttp import AiohttpSession

from handlers.start import router as start_router

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

load_dotenv()

dp = Dispatcher()


async def main():
    logger.info("Запускается")
    token = os.getenv("TG_TOKEN")
    if not token:
        raise ValueError("TG_TOKEN не найден в переменных окружения")
    proxy_url = os.getenv("TG_PROXY_URL")
    session = None
    if session:
        logger.info("Найден прокси URL %s", proxy_url)
        session = AiohttpSession(proxy=proxy_url)

    dp.include_router(start_router)
    bot = Bot(token=token, session=session)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
