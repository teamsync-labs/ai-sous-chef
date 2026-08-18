import hmac
import logging
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse
from sqlalchemy import select

from .api.error_handlers import log_request_validation_error
from .core.config import settings
from .core.logging import setup_logging
from .database.database import get_db
from .api import api

setup_logging(settings.LOG_LEVEL)

logger = logging.getLogger(__name__)

_DOCS_USER = "dev"
_DOCS_PASSWORD = "dev"
_docs_basic = HTTPBasic(auto_error=True)


def _require_docs_basic(
    credentials: Annotated[HTTPBasicCredentials, Depends(_docs_basic)],
) -> None:
    try:
        user_ok = hmac.compare_digest(credentials.username, _DOCS_USER)
        pass_ok = hmac.compare_digest(credentials.password, _DOCS_PASSWORD)
    except (TypeError, ValueError):
        user_ok = False
        pass_ok = False
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized",
            headers={"WWW-Authenticate": 'Basic realm="API docs"'},
        )


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.include_router(api.router)
app.add_exception_handler(
    RequestValidationError,
    log_request_validation_error,
)


@app.get("/docs", include_in_schema=False)
async def swagger_ui(_: Annotated[None, Depends(_require_docs_basic)]):
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{settings.APP_NAME} - Swagger UI",
    )


@app.get("/redoc", include_in_schema=False)
async def redoc_ui(_: Annotated[None, Depends(_require_docs_basic)]):
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=f"{settings.APP_NAME} - ReDoc",
    )


@app.get("/openapi.json", include_in_schema=False)
async def openapi_schema(_: Annotated[None, Depends(_require_docs_basic)]):
    return JSONResponse(app.openapi())


@app.get(
    "/health",
    summary="Проверка состояния сервиса",
    description=(
        "Эндпоинт для проверки работоспособности API и доступности БД. "
        "Используется для мониторинга и health-проверок "
        "(например, Docker/Kubernetes)."
    ),
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
