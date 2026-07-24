import logging

from fastapi import Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError

logger = logging.getLogger(__name__)


async def log_request_validation_error(
        request: Request,
        exc: RequestValidationError,
):
    errors = [
        {
            "location": ".".join(map(str, error.get("loc", ()))),
            "message": error.get("msg"),
            "type": error.get("type"),
        }
        for error in exc.errors()
    ]
    logger.warning(
        "Request validation failed: method=%s path=%s errors=%s",
        request.method,
        request.url.path,
        errors,
    )

    return await request_validation_exception_handler(request, exc)
