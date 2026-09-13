import logging
from typing import Any

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject, Message, CallbackQuery, Update

from services.api_client import latest_consent
from app.core.log_safe import mask_id

logger = logging.getLogger(__name__)


class ConsentMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message | CallbackQuery, data: dict[str, Any]):
        user_id = event.from_user.id if event.from_user else None
        logger.debug("Consent middleware: user_id=%s checking", mask_id(user_id))

        state: FSMContext = data.get("state")
        state_data = await state.get_data()

        if state and state_data.get("is_accept_consents"):
            logger.info("Consent middleware: user_id=%s consented (FSM cache), passing", mask_id(user_id))
            return await handler(event, data)

        logger.debug("Consent middleware: user_id=%s checking external consent (privacy, pdn)", mask_id(user_id))
        if await self.get_consent_info(user_id, "privacy") and await self.get_consent_info(user_id, "pdn"):
            logger.info("Consent middleware: user_id=%s consented (external), caching and passing", mask_id(user_id))
            await state.set_data({"is_accept_consents": True})
            return await handler(event, data)

        if self.is_command_start(event):
            logger.info("Consent middleware: user_id=%s /start, passing", mask_id(user_id))
            return await handler(event, data)

        if isinstance(event, CallbackQuery):
            logger.info("Consent middleware: user_id=%s consent callback, passing", mask_id(user_id))
            return await handler(event, data)

        logger.info("Consent middleware: user_id=%s not consented, blocking", mask_id(user_id))
        return await self.handle_unaccepted(event, data)

    async def get_consent_info(self, user_id: int, consent_type: str):
        data = await latest_consent(external_id=str(user_id), consent_type=consent_type)
        if not data.get("ok", False):
            return False
        journal = data.get("journal")
        if not journal:
            return False
        latest_journal = journal.get("latest")
        if not latest_journal:
            return False
        if latest_journal.get("action") != "granted":
            return False
        return True

    async def handle_unaccepted(self, event: Message | CallbackQuery, data: dict[str, Any]):
        user_id = event.from_user.id if event.from_user else None
        message = "Для доступа к боту необходимо ознакомиться и принять соглашения по команде /start"
        logger.info("Consent middleware: user_id=%s prompted to accept consent", mask_id(user_id))
        await event.answer(message)

    def is_command_start(self, event: Message | CallbackQuery):
        if isinstance(event, Message) and (event.text.startswith("/start") or event.text.startswith("/delete")):
            return True
        return False