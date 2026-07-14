import logging
from typing import Annotated

from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse
from sqlalchemy import select
from .core.config import settings
from .core.logging import setup_logging
from .database.database import get_db

setup_logging(settings.LOG_LEVEL)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs"
)


@app.get(
    "/health",
    summary="Проверка состояния сервера",
    description="Возвращает статус сервера и доступность БД. Используется для проверки, что backend работает и готов принимать запросы.",
)
async def health(db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        result = await db.execute(select(1))
        if result.scalar() == 1:
            logger.info("Успешный запрос на /health")
            return JSONResponse({"db": "ok"})
        else:
            logger.warning("Ошибочный запрос на /health: ответ от БД отличается от 1")
    except Exception as exc:
        logger.warning("Ошибочный запрос на /health: %s", exc)

    return JSONResponse({"db": "error"}, status_code=503)
