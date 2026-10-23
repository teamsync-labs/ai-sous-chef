import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .api_models import (
    ConsentChannel,
    ConsentProxyResult,
    ConsentRecordInput,
    ConsentWithdrawInput,
    validate_consent_identity,
)
from .deps import api_key_matches
from ..core.config import settings
from ..database.database import get_db
from ..services import consent_journal
from ..services import consent_subjects

router = APIRouter(prefix="/consent", tags=["Consent"])

logger = logging.getLogger(__name__)


@router.post("", response_model=ConsentProxyResult)
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


@router.get("/latest", response_model=ConsentProxyResult)
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


@router.post("/withdraw", response_model=ConsentProxyResult)
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


def _require_channel_api_key(channel: str | None, api_key: str | None) -> None:
    if channel == "bot":
        expected = settings.API_KEY_BOT
    elif channel == "app":
        expected = settings.API_KEY_APP
    else:
        expected = settings.API_KEY_SITE
    if not api_key_matches(api_key, expected):
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


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip() or None
    return request.client.host if request.client else None
