"""Прокси согласий на своём backend — журнал мокаем."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.consent_journal import ConsentJournalError

client = TestClient(app)

_RECORD = {
    "subject_id": "user_internal_1",
    "channel": "site",
    "consent_type": "analytics",
    "action": "granted",
}


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
    with patch(
        "app.api.api.consent_journal.record_consent",
        new=AsyncMock(return_value={"id": "evt-pdn"}),
    ) as mocked:
        response = client.post(
            "/app/api/consent",
            json={
                "subject_id": "user_internal_1",
                "channel": "bot",
                "consent_type": "pdn",
                "action": "granted",
            },
        )
    assert response.status_code == 200
    assert mocked.await_args.kwargs["consent_type"] == "pdn"
    assert mocked.await_args.kwargs["channel"] == "bot"


def test_latest_consent_check():
    latest = {"latest": {"action": "granted"}}
    with patch(
        "app.api.api.consent_journal.latest_consent",
        new=AsyncMock(return_value=latest),
    ) as mocked:
        response = client.get(
            "/app/api/consent/latest",
            params={
                "subject_id": "user_internal_1",
                "consent_type": "pdn",
                "channel": "bot",
            },
        )
    assert response.status_code == 200
    assert response.json()["journal"] == latest
    assert mocked.await_args.kwargs == {
        "subject_id": "user_internal_1",
        "consent_type": "pdn",
        "channel": "bot",
    }


def test_withdraw_with_erase():
    withdrawn = {"withdrawn": [{"id": "evt-2"}]}
    with patch(
        "app.api.api.consent_journal.withdraw_consent",
        new=AsyncMock(return_value=withdrawn),
    ) as mocked:
        response = client.post(
            "/app/api/consent/withdraw",
            json={
                "subject_id": "user_internal_1",
                "consent_type": "pdn",
                "channel": "bot",
                "erase": True,
            },
        )
    assert response.status_code == 200
    assert response.json()["journal"] == withdrawn
    assert mocked.await_args.kwargs["erase"] is True


def test_journal_error_returns_502():
    with patch(
        "app.api.api.consent_journal.record_consent",
        new=AsyncMock(side_effect=ConsentJournalError(
            "journal_error", status_code=401)),
    ):
        response = client.post("/app/api/consent", json=_RECORD)
    assert response.status_code == 502
    assert response.json()["detail"] == "consent_journal_error"
