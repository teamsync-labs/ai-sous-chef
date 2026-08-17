"""Внутренний id субъекта: get-or-create, без внешних id в журнале."""

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.database.database import get_db
from app.database.models import ConsentSubject
from app.main import app
from app.services.consent_subjects import get_or_create_id

client = TestClient(app)

_TELEGRAM_ID = "482917"
_INSTALL_ID = "install-7f3a2c1e"
_prev_get_db = None


def _run(coro):
    return asyncio.run(coro)


async def _override_get_db():
    yield MagicMock()


def setup_function():
    global _prev_get_db
    _prev_get_db = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _override_get_db


def teardown_function():
    if _prev_get_db is not None:
        app.dependency_overrides[get_db] = _prev_get_db
    else:
        app.dependency_overrides.pop(get_db, None)


def _memory_mapping():
    store: dict[tuple[str, str], str] = {}

    async def fake(_session, channel: str, external_id: str) -> str:
        key = (channel, external_id)
        if key not in store:
            store[key] = str(uuid.uuid4())
        return store[key]

    return store, fake


def test_same_telegram_id_returns_same_id():
    _, fake = _memory_mapping()
    with patch("app.api.api.consent_subjects.get_or_create_id", new=fake):
        first = client.post(
            "/app/api/consent/subject",
            json={"channel": "bot", "external_id": _TELEGRAM_ID},
        )
        second = client.post(
            "/app/api/consent/subject",
            json={"channel": "bot", "external_id": _TELEGRAM_ID},
        )
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    uuid.UUID(first.json()["id"])


def test_app_channel_accepts_install_id():
    _, fake = _memory_mapping()
    with patch("app.api.api.consent_subjects.get_or_create_id", new=fake):
        response = client.post(
            "/app/api/consent/subject",
            json={"channel": "app", "external_id": _INSTALL_ID},
        )
    assert response.status_code == 200
    uuid.UUID(response.json()["id"])


def test_bot_and_app_are_not_merged():
    _, fake = _memory_mapping()
    with patch("app.api.api.consent_subjects.get_or_create_id", new=fake):
        bot = client.post(
            "/app/api/consent/subject",
            json={"channel": "bot", "external_id": _TELEGRAM_ID},
        )
        app_resp = client.post(
            "/app/api/consent/subject",
            json={"channel": "app", "external_id": _TELEGRAM_ID},
        )
    assert bot.json()["id"] != app_resp.json()["id"]


def test_site_channel_rejected():
    response = client.post(
        "/app/api/consent/subject",
        json={"channel": "site", "external_id": "browser-uuid"},
    )
    assert response.status_code == 422


def test_subject_endpoint_does_not_call_journal():
    _, fake = _memory_mapping()
    with (
        patch("app.api.api.consent_subjects.get_or_create_id", new=fake),
        patch(
            "app.api.api.consent_journal.record_consent",
            new=AsyncMock(),
        ) as journal,
    ):
        response = client.post(
            "/app/api/consent/subject",
            json={"channel": "bot", "external_id": _TELEGRAM_ID},
        )
    assert response.status_code == 200
    journal.assert_not_awaited()


def test_journal_consent_gets_internal_id_not_telegram_id():
    _, fake = _memory_mapping()
    with patch("app.api.api.consent_subjects.get_or_create_id", new=fake):
        mapped = client.post(
            "/app/api/consent/subject",
            json={"channel": "bot", "external_id": _TELEGRAM_ID},
        )
    internal_id = mapped.json()["id"]
    with patch(
        "app.api.api.consent_journal.record_consent",
        new=AsyncMock(return_value={"id": "evt-1"}),
    ) as journal:
        response = client.post(
            "/app/api/consent",
            json={
                "subject_id": internal_id,
                "channel": "bot",
                "consent_type": "privacy",
                "action": "granted",
            },
        )
    assert response.status_code == 200
    kwargs = journal.await_args.kwargs
    assert kwargs["subject_id"] == internal_id
    assert kwargs["subject_id"] != _TELEGRAM_ID
    assert _TELEGRAM_ID not in kwargs.values()


def _session_mock():
    session = MagicMock()
    session.add = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


def test_get_or_create_returns_existing():
    existing = ConsentSubject(
        id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        channel="bot",
        external_id=_TELEGRAM_ID,
    )
    session = _session_mock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = existing
    session.execute = AsyncMock(return_value=result)

    got = _run(get_or_create_id(session, "bot", _TELEGRAM_ID))
    assert got == existing.id
    session.add.assert_not_called()
    session.commit.assert_not_awaited()


def test_get_or_create_inserts_when_missing():
    session = _session_mock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=result)

    got = _run(get_or_create_id(session, "app", _INSTALL_ID))
    session.add.assert_called_once()
    added = session.add.call_args[0][0]
    assert added.channel == "app"
    assert added.external_id == _INSTALL_ID
    assert got == added.id
    uuid.UUID(got)
    session.commit.assert_awaited_once()


def test_get_or_create_handles_insert_race():
    winner = ConsentSubject(
        id="11111111-2222-3333-4444-555555555555",
        channel="bot",
        external_id=_TELEGRAM_ID,
    )
    empty = MagicMock()
    empty.scalar_one_or_none.return_value = None
    after_conflict = MagicMock()
    after_conflict.scalar_one.return_value = winner

    session = _session_mock()
    session.execute = AsyncMock(side_effect=[empty, after_conflict])
    session.commit = AsyncMock(side_effect=IntegrityError("stmt", {}, Exception()))

    got = _run(get_or_create_id(session, "bot", _TELEGRAM_ID))
    assert got == winner.id
    session.rollback.assert_awaited_once()
