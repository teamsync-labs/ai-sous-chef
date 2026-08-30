import hmac
import logging
from typing import Annotated, Callable

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from .api_models import (
    BaseAPIModel,
    ConsentChannel,
    ConsentProxyResult,
    ConsentRecordInput,
    ConsentWithdrawInput,
    RecipesInput,
    RecipesResult,
    RecognizeInput,
    RecognizeResult,
    validate_consent_identity,
)

from ..core.ai_engine import get_ai_engine, AIServiceUnavailableError, ProductsNotFoundError
from ..core.config import settings
from ..database.database import get_db
from ..services import consent_journal
from ..services import consent_subjects

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/app/api",
    tags=["MVP API"]
)


async def proceed_ai(
        operation: str,
        ai_method: Callable[[], BaseAPIModel],
) -> BaseAPIModel:
    try:
        return await ai_method()

    except ValueError as exc:
        logger.warning(
            "AI request rejected: operation=%s reason=%s",
            operation,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="missing_input",
        ) from exc

    except AIServiceUnavailableError as exc:
        logger.error(
            "AI service unavailable: operation=%s reason=%s",
            operation,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ai_service_error",
        ) from exc
    except ProductsNotFoundError as exc:
        logger.warning(
            "Products not found: operation=%s reason=%s",
            operation,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="no_products_found",
        ) from exc
    except Exception:
        logger.exception("Unexpected API error: operation=%s", operation)
        raise


# OPTIMIZE: использовать асинхронные вызовы в ai_engine чтобы async def имело смысл

@router.post(
    "/recognize",
    response_model=RecognizeResult,
    summary="Распознать продукты",
    description=(
            "Распознаёт продукты по переданному изображению или текстовому описанию. "
            "Если передано изображение, продукты сначала определяются CV-моделью. "
            "Затем результат обрабатывается языковой моделью и преобразуется "
            "в нормализованный список продуктов.\n"
            "Возвращает список распознанных продуктов и уверенность модели. **Передавать только либо base_64, либо text**"))
async def recognize(
    recognize_input: RecognizeInput,
    x_api_key: Annotated[str | None, Header()] = None,
):
    _require_any_client_key(x_api_key)
    ai_engine = get_ai_engine()
    return await proceed_ai(
        "recognize",
        lambda: ai_engine.recognize_products(recognize_input),
    )


@router.post(
    "/recipes",
    response_model=RecipesResult,
    summary="Сгенерировать рецепты",
    description=(
            "Генерирует рецепты на основе переданного списка продуктов. "
            "Предполагается, что пользователь предварительно проверил и подтвердил "
            "список продуктов, полученный через эндпоинт `/recognize`.\n"
            "Возвращает список рецептов. Каждый рецепт содержит название "
            "и последовательность шагов приготовления."
    ))
async def recipes(
    recipes_input: RecipesInput,
    x_api_key: Annotated[str | None, Header()] = None,
):
    _require_any_client_key(x_api_key)
    ai_engine = get_ai_engine()
    return await proceed_ai(
        "recipes",
        lambda: ai_engine.generate_recipes(recipes_input),
    )


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip() or None
    return request.client.host if request.client else None


def _api_key_matches(provided: str | None, expected: str) -> bool:
    if not provided:
        return False
    try:
        return hmac.compare_digest(provided, expected)
    except (TypeError, ValueError):
        return False


def _require_any_client_key(api_key: str | None) -> None:
    bot_ok = _api_key_matches(api_key, settings.API_KEY_BOT)
    app_ok = _api_key_matches(api_key, settings.API_KEY_APP)
    if not (bot_ok or app_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized",
        )


def _require_channel_api_key(channel: str | None, api_key: str | None) -> None:
    if channel == "bot":
        expected = settings.API_KEY_BOT
    elif channel == "app":
        expected = settings.API_KEY_APP
    else:
        expected = settings.API_KEY_SITE
    if not _api_key_matches(api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized",
        )


async def _call_journal(operation, **kwargs) -> ConsentProxyResult:
    try:
        journal = await operation(**kwargs)
    except consent_journal.ConsentJournalError as exc:
        logger.warning("consent journal failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="consent_journal_error",
        ) from exc
    return ConsentProxyResult(ok=True, journal=journal)


async def _journal_subject_id(
    db: AsyncSession,
    channel: str | None,
    subject_id: str | None,
    external_id: str | None,
    *,
    create: bool = True,
) -> str | None:
    return await consent_subjects.resolve_journal_subject_id(
        db, channel, subject_id, external_id, create=create
    )


@router.post("/consent", response_model=ConsentProxyResult)
async def record_consent(
    body: ConsentRecordInput,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    x_api_key: Annotated[str | None, Header()] = None,
):
    _require_channel_api_key(body.channel, x_api_key)
    subject_id = await _journal_subject_id(
        db, body.channel, body.subject_id, body.external_id
    )
    return await _call_journal(
        consent_journal.record_consent,
        subject_id=subject_id,
        channel=body.channel,
        consent_type=body.consent_type,
        action=body.action,
        ip=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.get("/consent/latest", response_model=ConsentProxyResult)
async def latest_consent(
    consent_type: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    subject_id: str | None = None,
    external_id: str | None = None,
    channel: ConsentChannel | None = None,
    x_api_key: Annotated[str | None, Header()] = None,
):
    try:
        validate_consent_identity(channel, subject_id, external_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    _require_channel_api_key(channel, x_api_key)
    journal_subject_id = await _journal_subject_id(
        db, channel, subject_id, external_id
    )
    return await _call_journal(
        consent_journal.latest_consent,
        subject_id=journal_subject_id,
        consent_type=consent_type,
        channel=channel,
    )


@router.post("/consent/withdraw", response_model=ConsentProxyResult)
async def withdraw_consent(
    body: ConsentWithdrawInput,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    x_api_key: Annotated[str | None, Header()] = None,
):
    _require_channel_api_key(body.channel, x_api_key)
    subject_id = await _journal_subject_id(
        db,
        body.channel,
        body.subject_id,
        body.external_id,
        create=False,
    )
    if not subject_id:
        return ConsentProxyResult(ok=True, journal={"withdrawn": []})
    result = await _call_journal(
        consent_journal.withdraw_consent,
        subject_id=subject_id,
        consent_type=body.consent_type,
        channel=body.channel,
        erase=body.erase,
        ip=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    if body.channel in {"bot", "app"} and body.external_id:
        await consent_subjects.delete_by_channel_external(
            db, body.channel, body.external_id
        )
    return result
