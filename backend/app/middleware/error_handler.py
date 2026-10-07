"""Exception handlers: safe JSON bodies, never stack traces or secrets."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.errors import AppError, ConsentRequiredError
from app.integrations.errors import (
    IntegrationError,
    ProviderNotConfiguredError,
    ProviderUnavailableError,
)
from app.utils.error_codes import error_payload

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the app."""

    @app.exception_handler(ConsentRequiredError)
    async def consent_required_handler(
        _: Request, exc: ConsentRequiredError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(exc.code, exc.detail, exc.details or None),
        )

    @app.exception_handler(ProviderNotConfiguredError)
    async def provider_not_configured(
        _: Request, exc: ProviderNotConfiguredError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content=error_payload("NOT_CONFIGURED", exc.message),
        )

    @app.exception_handler(ProviderUnavailableError)
    async def provider_unavailable(
        _: Request, exc: ProviderUnavailableError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content=error_payload("PROVIDER_UNAVAILABLE", exc.message),
        )

    @app.exception_handler(IntegrationError)
    async def integration_error(_: Request, exc: IntegrationError) -> JSONResponse:
        logger.warning("Integration error: %s", type(exc).__name__)
        return JSONResponse(
            status_code=502,
            content=error_payload(exc.code, exc.message),
        )

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        headers = dict(exc.headers or {})
        if exc.status_code == 401:
            headers.setdefault("WWW-Authenticate", "Bearer")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=headers or None,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Never echo submitted values (they may contain passwords or PII).
        errors = [
            {
                "field": ".".join(str(part) for part in error.get("loc", [])),
                "message": error.get("msg", "Invalid value."),
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={"detail": "Validation failed.", "errors": errors},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Something went wrong. Please try again."},
        )
