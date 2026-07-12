from fastapi import FastAPI
from starlette.responses import JSONResponse
from .core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs"
)


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})
