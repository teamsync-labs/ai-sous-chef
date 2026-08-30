import os

import httpx

API_BASE = os.getenv("API_BASE", "http://localhost:8000/app/api")
API_KEY_BOT = os.getenv("API_KEY_BOT", "")


def _api_headers() -> dict[str, str]:
    return {"X-Api-Key": API_KEY_BOT}


async def recognize(base64: str | None = None, text: str | None = None) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{API_BASE}/recognize",
            headers=_api_headers(),
            json={"img_base64": base64, "text": text}
        )
        response.raise_for_status()
        return response.json()


async def get_recipes(products: list[str]) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{API_BASE}/recipes",
            headers=_api_headers(),
            json={"products": products}
        )
        response.raise_for_status()
        return response.json()


async def record_consent(
    *,
    external_id: str,
    consent_type: str,
    action: str,
    channel: str = "bot",
) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            f"{API_BASE}/consent",
            headers=_api_headers(),
            json={
                "channel": channel,
                "external_id": external_id,
                "consent_type": consent_type,
                "action": action,
            },
        )
        response.raise_for_status()
        return response.json()


async def latest_consent(
    *,
    external_id: str,
    consent_type: str,
    channel: str = "bot",
) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            f"{API_BASE}/consent/latest",
            headers=_api_headers(),
            params={
                "channel": channel,
                "external_id": external_id,
                "consent_type": consent_type,
            },
        )
        response.raise_for_status()
        return response.json()


async def withdraw_consent(
    *,
    external_id: str,
    consent_type: str | None = None,
    channel: str = "bot",
    erase: bool = True,
) -> dict:
    payload: dict = {
        "channel": channel,
        "external_id": external_id,
        "erase": erase,
    }
    if consent_type:
        payload["consent_type"] = consent_type
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            f"{API_BASE}/consent/withdraw",
            headers=_api_headers(),
            json=payload,
        )
        response.raise_for_status()
        return response.json()
