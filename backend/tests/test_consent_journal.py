"""HTTP-клиент журнала согласий — без живой сети."""

import asyncio
import json
from unittest.mock import patch

import httpx
import pytest

from app.services.consent_journal import (
    ConsentJournalError,
    latest_consent,
    record_consent,
    withdraw_consent,
)


def _run(coro):
    return asyncio.run(coro)


def _patch_transport(handler):
    transport = httpx.MockTransport(handler)
    original = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = transport
        return original(*args, **kwargs)

    return patch("app.services.consent_journal.httpx.AsyncClient", side_effect=factory)


def test_record_consent_posts_bearer_and_subject_id():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["authorization"] = request.headers.get("authorization")
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"id": "evt-1", "consented_at": "2026-08-17T00:00:00.000Z", "document_version_id": "ver-1"},
        )

    async def go():
        with _patch_transport(handler):
            return await record_consent(
                subject_id="user_internal_1",
                channel="site",
                consent_type="analytics",
                action="granted",
                ip="203.0.113.10",
                user_agent="pytest",
            )

    result = _run(go())
    assert result["id"] == "evt-1"
    assert captured["method"] == "POST"
    assert captured["path"] == "/v1/consents"
    assert captured["authorization"] == "Bearer test-key"
    assert captured["body"] == {
        "subject_id": "user_internal_1",
        "channel": "site",
        "consent_type": "analytics",
        "action": "granted",
        "ip": "203.0.113.10",
        "user_agent": "pytest",
    }


def test_latest_consent_get_query():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["query"] = dict(request.url.params)
        return httpx.Response(200, json={"latest": {"action": "granted"}})

    async def go():
        with _patch_transport(handler):
            return await latest_consent(
                subject_id="user_internal_1",
                consent_type="pdn",
                channel="bot",
            )

    result = _run(go())
    assert result["latest"]["action"] == "granted"
    assert captured["method"] == "GET"
    assert captured["path"] == "/v1/consents/latest"
    assert captured["query"] == {
        "subject_id": "user_internal_1",
        "consent_type": "pdn",
        "channel": "bot",
    }


def test_withdraw_consent_posts_erase():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"withdrawn": [{"id": "evt-2"}]})

    async def go():
        with _patch_transport(handler):
            return await withdraw_consent(
                subject_id="user_internal_1",
                consent_type="pdn",
                channel="bot",
                erase=True,
            )

    result = _run(go())
    assert result["withdrawn"][0]["id"] == "evt-2"
    assert captured["path"] == "/v1/consents/withdraw"
    assert captured["body"] == {
        "subject_id": "user_internal_1",
        "erase": True,
        "consent_type": "pdn",
        "channel": "bot",
    }


def test_journal_http_error_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "unauthorized"})

    async def go():
        with _patch_transport(handler):
            await record_consent(
                subject_id="user_internal_1",
                channel="site",
                consent_type="analytics",
                action="granted",
            )

    with pytest.raises(ConsentJournalError) as exc:
        _run(go())
    assert exc.value.status_code == 401
    assert exc.value.body == {"error": "unauthorized"}


def test_journal_unreachable_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    async def go():
        with _patch_transport(handler):
            await latest_consent(subject_id="x", consent_type="pdn")

    with pytest.raises(ConsentJournalError, match="journal_unreachable"):
        _run(go())
