from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from ..core.config import settings

engine = create_async_engine(settings.DATABASE_URL)

session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session
