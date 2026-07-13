import logging

from fastapi import FastAPI
from starlette.responses import JSONResponse
from .core.config import settings
from .core.logging import setup_logging

setup_logging(settings.LOG_LEVEL)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs"
)


@app.get("/health")
async def health():
    logger.info("Успешный запрос на /health")
    return JSONResponse({"status": "ok"})
