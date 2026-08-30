"""Маппинг bot/app внутри прокси: в журнал только внутренний id."""

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

_BOT_HEADERS = {"X-Api-Key": "test-bot-key"}
_APP_HEADERS = {"X-Api-Key": "test-app-key"}
_SITE_HEADERS = {"X-Api-Key": "test-site-key"}
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


def test_subject_endpoint_removed():
    response = client.post(
        "/app/api/consent/subject",
        json={"channel": "bot", "external_id": _TELEGRAM_ID},
    )
    assert response.status_code == 404


def test_same_telegram_id_maps_to_same_journal_subject():
    _, fake = _memory_mapping()
    captured: list[str] = []
    with (
        patch("app.api.api.consent_subjects.get_or_create_id", new=fake),
        patch(
            "app.api.api.consent_journal.record_consent",
            new=AsyncMock(return_value={"id": "evt"}),
        ) as journal,
    ):
        first = client.post(
            "/app/api/consent",
            headers=_BOT_HEADERS,
            json={
                "channel": "bot",
                "external_id": _TELEGRAM_ID,
                "consent_type": "privacy",
                "action": "granted",
            },
        )
        second = client.post(
            "/app/api/consent",
            headers=_BOT_HEADERS,
            json={
                "channel": "bot",
                "external_id": _TELEGRAM_ID,
                "consent_type": "pdn",
                "action": "granted",
            },
        )
        captured = [
            journal.await_args_list[0].kwargs["subject_id"],
            journal.await_args_list[1].kwargs["subject_id"],
        ]
    assert first.status_code == 200
    assert second.status_code == 200
    assert captured[0] == captured[1]
    uuid.UUID(captured[0])
    assert captured[0] != _TELEGRAM_ID
    assert _TELEGRAM_ID not in journal.await_args_list[0].kwargs.values()


def test_app_channel_maps_install_id():
    _, fake = _memory_mapping()
    with (
        patch("app.api.api.consent_subjects.get_or_create_id", new=fake),
        patch(
            "app.api.api.consent_journal.record_consent",
            new=AsyncMock(return_value={"id": "evt"}),
        ) as journal,
    ):
        response = client.post(
            "/app/api/consent",
            headers=_APP_HEADERS,
            json={
                "channel": "app",
                "external_id": _INSTALL_ID,
                "consent_type": "pdn",
                "action": "granted",
            },
        )
    assert response.status_code == 200
    journal_subject = journal.await_args.kwargs["subject_id"]
    uuid.UUID(journal_subject)
    assert journal_subject != _INSTALL_ID
    assert _INSTALL_ID not in journal.await_args.kwargs.values()


def test_bot_and_app_are_not_merged():
    _, fake = _memory_mapping()
    with (
        patch("app.api.api.consent_subjects.get_or_create_id", new=fake),
        patch(
            "app.api.api.consent_journal.record_consent",
            new=AsyncMock(return_value={"id": "evt"}),
        ) as journal,
    ):
        client.post(
            "/app/api/consent",
            headers=_BOT_HEADERS,
            json={
                "channel": "bot",
                "external_id": _TELEGRAM_ID,
                "consent_type": "pdn",
                "action": "granted",
            },
        )
        client.post(
            "/app/api/consent",
            headers=_APP_HEADERS,
            json={
                "channel": "app",
                "external_id": _TELEGRAM_ID,
                "consent_type": "pdn",
                "action": "granted",
            },
        )
    bot_id = journal.await_args_list[0].kwargs["subject_id"]
    app_id = journal.await_args_list[1].kwargs["subject_id"]
    assert bot_id != app_id


def test_site_does_not_use_mapping_table():
    with (
        patch(
            "app.api.api.consent_subjects.get_or_create_id",
            new=AsyncMock(),
        ) as mapped,
        patch(
            "app.api.api.consent_journal.record_consent",
            new=AsyncMock(return_value={"id": "evt"}),
        ) as journal,
    ):
        response = client.post(
            "/app/api/consent",
            headers=_SITE_HEADERS,
            json={
                "channel": "site",
                "subject_id": "browser-uuid",
                "consent_type": "analytics",
                "action": "granted",
            },
        )
    assert response.status_code == 200
    mapped.assert_not_awaited()
    assert journal.await_args.kwargs["subject_id"] == "browser-uuid"


def test_bot_rejects_subject_id():
    response = client.post(
        "/app/api/consent",
        json={
            "channel": "bot",
            "subject_id": "should-not-work",
            "consent_type": "privacy",
            "action": "granted",
        },
    )
    assert response.status_code == 422


def test_site_rejects_external_id():
    response = client.post(
        "/app/api/consent",
        json={
            "channel": "site",
            "external_id": _TELEGRAM_ID,
            "consent_type": "analytics",
            "action": "granted",
        },
    )
    assert response.status_code == 422


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


def test_get_id_returns_none_when_missing():
    from app.services.consent_subjects import get_id

    session = _session_mock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=result)
    assert _run(get_id(session, "bot", _TELEGRAM_ID)) is None


def test_delete_by_channel_external_commits():
    from app.services.consent_subjects import delete_by_channel_external

    session = _session_mock()
    result = MagicMock()
    result.rowcount = 1
    session.execute = AsyncMock(return_value=result)
    assert _run(delete_by_channel_external(session, "bot", _TELEGRAM_ID)) is True
    session.commit.assert_awaited_once()
