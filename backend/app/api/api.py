import logging
from typing import Annotated, Callable

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from .api_models import (
    BaseAPIModel,
    ConsentProxyResult,
    ConsentRecordInput,
    ConsentSubjectInput,
    ConsentSubjectResult,
    ConsentWithdrawInput,
    RecipesInput,
    RecipesResult,
    RecognizeInput,
    RecognizeResult,
)

from ..core.ai_engine import get_ai_engine, AIServiceUnavailableError, ProductsNotFoundError
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
async def recognize(recognize_input: RecognizeInput):
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
async def recipes(recipes_input: RecipesInput):
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


@router.post("/consent/subject", response_model=ConsentSubjectResult)
async def get_consent_subject(
    body: ConsentSubjectInput,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    subject_id = await consent_subjects.get_or_create_id(
        db, body.channel, body.external_id
    )
    return ConsentSubjectResult(id=subject_id)


@router.post("/consent", response_model=ConsentProxyResult)
async def record_consent(body: ConsentRecordInput, request: Request):
    return await _call_journal(
        consent_journal.record_consent,
        subject_id=body.subject_id,
        channel=body.channel,
        consent_type=body.consent_type,
        action=body.action,
        ip=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.get("/consent/latest", response_model=ConsentProxyResult)
async def latest_consent(
    subject_id: str,
    consent_type: str,
    channel: str | None = None,
):
    return await _call_journal(
        consent_journal.latest_consent,
        subject_id=subject_id,
        consent_type=consent_type,
        channel=channel,
    )


@router.post("/consent/withdraw", response_model=ConsentProxyResult)
async def withdraw_consent(body: ConsentWithdrawInput, request: Request):
    return await _call_journal(
        consent_journal.withdraw_consent,
        subject_id=body.subject_id,
        consent_type=body.consent_type,
        channel=body.channel,
        erase=body.erase,
        ip=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
