"""Get-or-create внутреннего id субъекта для журнала согласий."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import ConsentSubject


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
