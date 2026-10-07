"""Document routes: upload, list, private download and delete."""

from __future__ import annotations

from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, File, Form, UploadFile, status
from fastapi.responses import Response

from app.dependencies import CurrentUser, DbDep, StorageDep
from app.schemas.auth import MessageResponse
from app.schemas.document import DocumentOut, DocumentType
from app.services import document_service

application_documents_router = APIRouter(prefix="/applications", tags=["documents"])
documents_router = APIRouter(prefix="/documents", tags=["documents"])


def _content_disposition(filename: str) -> str:
    """Build a safe Content-Disposition header for the display filename."""
    ascii_name = filename.encode("ascii", "ignore").decode("ascii") or "document"
    return (
        f'attachment; filename="{ascii_name}"; '
        f"filename*=UTF-8''{quote(filename, safe='')}"
    )


@application_documents_router.post(
    "/{application_id}/documents",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document",
)
async def upload_document(
    application_id: str,
    current_user: CurrentUser,
    db: DbDep,
    storage: StorageDep,
    document_type: Annotated[DocumentType, Form()],
    file: Annotated[UploadFile, File()],
) -> DocumentOut:
    return await document_service.upload_document(
        db, storage, current_user, application_id, document_type, file
    )


@application_documents_router.get(
    "/{application_id}/documents",
    response_model=list[DocumentOut],
    summary="List documents of an application",
)
async def list_documents(
    application_id: str, current_user: CurrentUser, db: DbDep
) -> list[DocumentOut]:
    return await document_service.list_documents(db, current_user, application_id)


@documents_router.get(
    "/{document_id}/download",
    summary="Download a document (private, authenticated)",
)
async def download_document(
    document_id: str, current_user: CurrentUser, db: DbDep, storage: StorageDep
) -> Response:
    data, mime_type, filename = await document_service.download_document(
        db, storage, current_user, document_id
    )
    return Response(
        content=data,
        media_type=mime_type,
        headers={
            "Content-Disposition": _content_disposition(filename),
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
        },
    )


@documents_router.delete(
    "/{document_id}",
    response_model=MessageResponse,
    summary="Delete a document",
)
async def delete_document(
    document_id: str, current_user: CurrentUser, db: DbDep, storage: StorageDep
) -> MessageResponse:
    result = await document_service.delete_document(
        db, storage, current_user, document_id
    )
    return MessageResponse(**result)
