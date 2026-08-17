"""Прокси согласий на своём backend — журнал мокаем."""

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.database.database import get_db
from app.main import app
from app.services.consent_journal import ConsentJournalError

client = TestClient(app)

_RECORD = {
    "subject_id": "user_internal_1",
    "channel": "site",
    "consent_type": "analytics",
    "action": "granted",
}

_prev_get_db = None


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


def test_record_consent_proxies_to_journal():
    recorded = {"id": "evt-1"}
    with patch(
        "app.api.api.consent_journal.record_consent",
        new=AsyncMock(return_value=recorded),
    ) as mocked:
        response = client.post("/app/api/consent", json=_RECORD)
    assert response.status_code == 200
    assert response.json() == {"ok": True, "journal": recorded}
    kwargs = mocked.await_args.kwargs
    assert kwargs["subject_id"] == "user_internal_1"
    assert kwargs["channel"] == "site"
    assert kwargs["consent_type"] == "analytics"
    assert kwargs["action"] == "granted"


def test_record_pdn_granted():
    mapped_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    with (
        patch(
            "app.api.api.consent_subjects.get_or_create_id",
            new=AsyncMock(return_value=mapped_id),
        ),
        patch(
            "app.api.api.consent_journal.record_consent",
            new=AsyncMock(return_value={"id": "evt-pdn"}),
        ) as mocked,
    ):
        response = client.post(
            "/app/api/consent",
            json={
                "external_id": "482917",
                "channel": "bot",
                "consent_type": "pdn",
                "action": "granted",
            },
        )
    assert response.status_code == 200
    assert mocked.await_args.kwargs["consent_type"] == "pdn"
    assert mocked.await_args.kwargs["channel"] == "bot"
    assert mocked.await_args.kwargs["subject_id"] == mapped_id


def test_latest_consent_check():
    mapped_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    latest = {"latest": {"action": "granted"}}
    with (
        patch(
            "app.api.api.consent_subjects.get_or_create_id",
            new=AsyncMock(return_value=mapped_id),
        ),
        patch(
            "app.api.api.consent_journal.latest_consent",
            new=AsyncMock(return_value=latest),
        ) as mocked,
    ):
        response = client.get(
            "/app/api/consent/latest",
            params={
                "external_id": "482917",
                "consent_type": "pdn",
                "channel": "bot",
            },
        )
    assert response.status_code == 200
    assert response.json()["journal"] == latest
    assert mocked.await_args.kwargs == {
        "subject_id": mapped_id,
        "consent_type": "pdn",
        "channel": "bot",
    }


def test_withdraw_with_erase():
    mapped_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    withdrawn = {"withdrawn": [{"id": "evt-2"}]}
    with (
        patch(
            "app.api.api.consent_subjects.get_or_create_id",
            new=AsyncMock(return_value=mapped_id),
        ),
        patch(
            "app.api.api.consent_journal.withdraw_consent",
            new=AsyncMock(return_value=withdrawn),
        ) as mocked,
    ):
        response = client.post(
            "/app/api/consent/withdraw",
            json={
                "external_id": "482917",
                "consent_type": "pdn",
                "channel": "bot",
                "erase": True,
            },
        )
    assert response.status_code == 200
    assert response.json()["journal"] == withdrawn
    assert mocked.await_args.kwargs["erase"] is True
    assert mocked.await_args.kwargs["subject_id"] == mapped_id


def test_journal_error_returns_502():
    with patch(
        "app.api.api.consent_journal.record_consent",
        new=AsyncMock(side_effect=ConsentJournalError(
            "journal_error", status_code=401)),
    ):
        response = client.post("/app/api/consent", json=_RECORD)
    assert response.status_code == 502
    assert response.json()["detail"] == "consent_journal_error"
