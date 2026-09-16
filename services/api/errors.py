from __future__ import annotations

import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


error_logger = logging.getLogger("applyintel.errors")


class APIError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


def request_id_from_state(request: Request) -> str:
    return getattr(request.state, "request_id", str(uuid.uuid4()))


def error_response(request: Request, status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id_from_state(request),
            }
        },
    )


async def api_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, APIError):
        raise exc
    return error_response(request, exc.status_code, exc.code, exc.message)


async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    error_logger.exception(
        "Unhandled API error request_id=%s path=%s",
        request_id_from_state(request),
        request.url.path,
        exc_info=exc,
    )
    return error_response(request, 500, "INTERNAL_ERROR", "An unexpected error occurred.")


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(Exception, internal_error_handler)
