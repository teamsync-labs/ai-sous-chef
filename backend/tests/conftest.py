"""
Фикстуры для тестов Telegram-бота (start.py).

Задача: не дёргать реальные TG API и Consent API. Поэтому:
- Bot/Message/CallbackQuery подменяются MagicMock'ами;
- record_consent мокается по месту импорта в handlers.start;
- состояния живут в реальном MemoryStorage (новом на каждый тест).
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

# start.py использует «плоские» импорты (from services.api_client import ...),
# поэтому backend/bot должен быть в sys.path.
BOT_DIR = Path(__file__).resolve().parent.parent / "bot"
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))


@pytest.fixture
def storage() -> MemoryStorage:
    """Свежее MemoryStorage на каждый тест — состояния не протекают."""
    return MemoryStorage()


@pytest.fixture
async def state(storage: MemoryStorage) -> FSMContext:
    """Изолированный FSMContext для одного тестового пользователя."""
    key = StorageKey(bot_id=1, chat_id=1, user_id=42)
    return FSMContext(storage=storage, key=key)


@pytest.fixture
def mock_record_consent():
    """
    Мок record_consent по месту импорта в handlers.start.

    В start.py стоит `from services.api_client import record_consent`,
    поэтому патчить надо `handlers.start.record_consent`, а не
    `services.api_client.record_consent`.
    """
    with patch(
        "handlers.start.record_consent",
        new_callable=AsyncMock,
        return_value={"ok": True},
    ) as mocked:
        yield mocked


@pytest.fixture
def make_message():
    """Фабрика фейкового Message. По умолчанию — команда /start."""

    def _make(text: str = "/start"):
        msg = MagicMock()
        msg.text = text
        msg.answer = AsyncMock()
        msg.reply = AsyncMock()
        msg.delete = AsyncMock()
        msg.from_user = MagicMock(id=42)
        return msg

    return _make


@pytest.fixture
def make_callback():
    """Фабрика фейкового CallbackQuery. consent=True — «Согласен»."""

    def _make(question: int = 1, consent: bool = True):
        from keyboards.consent import ConsentCallback

        cb = MagicMock()
        cb.data = ConsentCallback(question=question, consent=consent).pack()
        cb.answer = AsyncMock()
        cb.from_user = MagicMock(id=42)
        cb.message = MagicMock()
        cb.message.answer = AsyncMock()
        cb.message.delete = AsyncMock()
        return cb

    return _make


@pytest.fixture
def callback_data():
    """Фабрика ConsentCallback для передачи в хендлер вторым аргументом."""

    def _make(question: int = 1, consent: bool = True):
        from keyboards.consent import ConsentCallback

        return ConsentCallback(question=question, consent=consent)

    return _make