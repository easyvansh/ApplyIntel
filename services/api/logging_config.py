from __future__ import annotations

import json
import logging
import re
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response


REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]+$")

request_logger = logging.getLogger("applyintel.requests")
if not request_logger.handlers:
    request_handler = logging.StreamHandler()
    request_handler.setFormatter(logging.Formatter("%(message)s"))
    request_logger.addHandler(request_handler)
request_logger.setLevel(logging.INFO)
request_logger.propagate = False


def get_request_id(request: Request) -> str:
    supplied_request_id = request.headers.get("X-Request-ID", "").strip()
    if (
        supplied_request_id
        and len(supplied_request_id) <= 128
        and REQUEST_ID_PATTERN.fullmatch(supplied_request_id)
    ):
        return supplied_request_id
    return str(uuid.uuid4())


async def request_logging_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = get_request_id(request)
    request.state.request_id = request_id
    started_at = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        log_method = request_logger.error if status_code >= 500 else request_logger.info
        log_method(
            json.dumps(
                {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": status_code,
                    "duration_ms": duration_ms,
                },
                separators=(",", ":"),
            )
        )


def configure_request_logging(app: FastAPI) -> None:
    app.middleware("http")(request_logging_middleware)
