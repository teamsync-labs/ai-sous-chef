import logging
from typing import Any

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject, Message, CallbackQuery, Update

logger = logging.getLogger(__name__)


class ConsentMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message | CallbackQuery, data: dict[str, Any]):
        user_id = event.from_user.id if event.from_user else None

        if self.is_command_start(event):
            logger.info("Consent middleware: user_id=%s /start, passing through", user_id)
            return await handler(event, data)

        state: FSMContext = data.get("state")

        if state is None:
            logger.warning("Consent middleware: user_id=%s FSM state missing, blocking", user_id)
            await self.handle_unaccepted(event, data)
            return

        state_data = await state.get_data()

        if not state_data.get("is_accept_consent"):
            logger.info("Consent middleware: user_id=%s not consented, blocking", user_id)
            await self.handle_unaccepted(event, data)
            return

        logger.debug("Consent middleware: user_id=%s consented, passing", user_id)
        return await handler(event, data)

    async def handle_unaccepted(self, event: Message | CallbackQuery, data: dict[str, Any]):
        user_id = event.from_user.id if event.from_user else None
        message = "Для доступа к боту необходимо ознакомиться и принять соглашения по команде /start"
        logger.info("Consent middleware: user_id=%s prompted to accept consent", user_id)
        await event.answer(message)

    def is_command_start(self, event: Message | CallbackQuery):
        if isinstance(event, Message) and event.text.startswith("/start"):
            return True
        return False
