import os

import httpx

API_BASE = os.getenv("API_BASE", "http://localhost:8000/app/api")


async def recognize(base64: str | None = None, text: str | None = None) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{API_BASE}/recognize",
            json={"base64": base64, "text": text}
        )
        response.raise_for_status()
        return response.json()


async def get_recipes(products: list[str]) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{API_BASE}/recipes",
            json={"products": products}
        )
        response.raise_for_status()
        return response.json()
