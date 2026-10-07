"""Structured request logging middleware (no bodies, no tokens)."""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any, Awaitable, Callable

from fastapi import Request, Response

logger = logging.getLogger("e_sewasathi.request")


async def request_logging_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Log one structured JSON line per request with timing and status."""
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:16]
    request.state.request_id = request_id
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.error(
            json.dumps(
                {
                    "event": "http_request",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": 500,
                    "duration_ms": duration_ms,
                }
            )
        )
        raise

    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    payload: dict[str, Any] = {
        "event": "http_request",
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "duration_ms": duration_ms,
    }
    if response.status_code >= 500:
        logger.error(json.dumps(payload))
    elif response.status_code >= 400:
        logger.warning(json.dumps(payload))
    else:
        logger.info(json.dumps(payload))
    return response
