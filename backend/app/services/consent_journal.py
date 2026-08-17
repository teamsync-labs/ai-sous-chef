"""HTTP-клиент журнала согласий."""

from __future__ import annotations

from typing import Any

import httpx

from ..core.config import settings


class ConsentJournalError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None, body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


def _http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.CONSENT_JOURNAL_URL.rstrip("/"),
        headers={
            "Authorization": f"Bearer {settings.CONSENT_JOURNAL_API_KEY}",
            "Content-Type": "application/json",
        },
        timeout=10.0,
    )


async def record_consent(
    *,
    subject_id: str,
    channel: str,
    consent_type: str,
    action: str,
    ip: str | None = None,
    user_agent: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "subject_id": subject_id,
        "channel": channel,
        "consent_type": consent_type,
        "action": action,
    }
    if ip:
        payload["ip"] = ip
    if user_agent:
        payload["user_agent"] = user_agent
    return await _request("POST", "/v1/consents", json=payload)


async def latest_consent(
    *,
    subject_id: str,
    consent_type: str,
    channel: str | None = None,
) -> dict[str, Any]:
    params: dict[str, str] = {
        "subject_id": subject_id,
        "consent_type": consent_type,
    }
    if channel:
        params["channel"] = channel
    return await _request("GET", "/v1/consents/latest", params=params)


async def withdraw_consent(
    *,
    subject_id: str,
    consent_type: str | None = None,
    channel: str | None = None,
    erase: bool = False,
    ip: str | None = None,
    user_agent: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "subject_id": subject_id,
        "erase": erase,
    }
    if consent_type:
        payload["consent_type"] = consent_type
    if channel:
        payload["channel"] = channel
    if ip:
        payload["ip"] = ip
    if user_agent:
        payload["user_agent"] = user_agent
    return await _request("POST", "/v1/consents/withdraw", json=payload)


async def _request(
    method: str,
    path: str,
    *,
    json: dict[str, Any] | None = None,
    params: dict[str, str] | None = None,
) -> dict[str, Any]:
    try:
        async with _http_client() as client:
            response = await client.request(method, path, json=json, params=params)
    except httpx.HTTPError as exc:
        raise ConsentJournalError("journal_unreachable") from exc

    if response.status_code >= 400:
        try:
            body: Any = response.json()
        except ValueError:
            body = response.text
        raise ConsentJournalError(
            "journal_error",
            status_code=response.status_code,
            body=body,
        )

    if not response.content:
        return {}
    return response.json()
