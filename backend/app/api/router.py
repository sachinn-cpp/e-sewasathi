"""API router aggregation for e-SewaSathi."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import applications, auth, documents, users

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(applications.router)
api_router.include_router(documents.application_documents_router)
api_router.include_router(documents.documents_router)
