"""Security headers middleware."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from fastapi import Request, Response

from app.config import get_settings


async def security_headers_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Attach safe response headers to every HTTP response."""
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; frame-ancestors 'none'; base-uri 'self'",
    )
    if get_settings().demo_mode:
        response.headers.setdefault("X-Demo-Mode", "true")
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        response.headers.setdefault("X-Request-ID", str(request_id))
    return response
