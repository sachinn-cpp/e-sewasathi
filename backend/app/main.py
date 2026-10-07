"""e-SewaSathi API entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.router import api_router
from app.config import get_settings
from app.database.indexes import ensure_indexes
from app.database.mongodb import close_db, connect_db, get_database
from app.middleware.error_handler import register_exception_handlers
from app.middleware.request_logging import request_logging_middleware
from app.middleware.security_headers import security_headers_middleware

logger = logging.getLogger("e_sewasathi")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await connect_db()
    await ensure_indexes(get_database())
    yield
    await close_db()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description=(
            "Your trusted AI companion for completing government services. "
            "Phase 2 adds the agent workflow, consent, portal submission, "
            "status tracking, escalation and human-helper tooling."
        ),
        version=__version__,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["Content-Disposition", "X-Demo-Mode", "X-Request-ID"],
        max_age=600,
    )

    app.middleware("http")(request_logging_middleware)
    app.middleware("http")(security_headers_middleware)
    register_exception_handlers(app)

    @app.get(f"{settings.api_prefix}/health", tags=["health"], summary="Health check")
    async def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "service": settings.app_name,
            "version": __version__,
            "environment": settings.environment,
            "demo_mode": settings.demo_mode,
        }

    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
