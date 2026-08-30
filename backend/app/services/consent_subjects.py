"""Get-or-create внутреннего id субъекта для журнала согласий."""

from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import ConsentSubject

_MAPPED_CHANNELS = frozenset({"bot", "app"})


async def get_or_create_id(
    session: AsyncSession,
    channel: str,
    external_id: str,
) -> str:
    stmt = select(ConsentSubject).where(
        ConsentSubject.channel == channel,
        ConsentSubject.external_id == external_id,
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is not None:
        return existing.id

    row = ConsentSubject(
        id=str(uuid.uuid4()),
        channel=channel,
        external_id=external_id,
    )
    session.add(row)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        existing = (await session.execute(stmt)).scalar_one()
        return existing.id
    return row.id


async def get_id(
    session: AsyncSession,
    channel: str,
    external_id: str,
) -> str | None:
    stmt = select(ConsentSubject.id).where(
        ConsentSubject.channel == channel,
        ConsentSubject.external_id == external_id,
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def delete_by_channel_external(
    session: AsyncSession,
    channel: str,
    external_id: str,
) -> bool:
    result = await session.execute(
        delete(ConsentSubject).where(
            ConsentSubject.channel == channel,
            ConsentSubject.external_id == external_id,
        )
    )
    await session.commit()
    return (result.rowcount or 0) > 0


async def resolve_journal_subject_id(
    session: AsyncSession,
    channel: str | None,
    subject_id: str | None,
    external_id: str | None,
    *,
    create: bool = True,
) -> str | None:
    if channel in _MAPPED_CHANNELS:
        external = external_id or ""
        if create:
            return await get_or_create_id(session, channel, external)
        return await get_id(session, channel, external)
    return subject_id or ""
