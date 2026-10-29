import hmac

from fastapi import HTTPException, status

from ..core.config import settings


def api_key_matches(provided: str | None, expected: str) -> bool:
    if not provided:
        return False
    try:
        return hmac.compare_digest(provided, expected)
    except (TypeError, ValueError):
        return False


def require_any_client_key(api_key: str | None) -> None:
    bot_ok = api_key_matches(api_key, settings.API_KEY_BOT)
    app_ok = api_key_matches(api_key, settings.API_KEY_APP)
    if not (bot_ok or app_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized",
        )
