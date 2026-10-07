"""Document service: validated uploads into private storage plus audit."""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timezone
from typing import Any, Mapping

from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase
from starlette.datastructures import UploadFile

from app.database.collections import APPLICATIONS, DOCUMENTS
from app.errors import AppError, NotFoundError
from app.integrations.storage.base import StorageAdapter, StorageError
from app.schemas.document import DocumentOut, DocumentType, ValidationStatus
from app.schemas.user import UserContext
from app.services import application_service, audit_service, consent_service
from app.utils.file_validation import FileValidationError, validate_upload
from app.utils.validators import safe_filename

logger = logging.getLogger(__name__)

_READ_CHUNK_SIZE = 1024 * 1024


def serialize_document(doc: Mapping[str, Any]) -> DocumentOut:
    """Convert a raw document record into the public schema."""
    return DocumentOut(
        id=str(doc["_id"]),
        application_id=str(doc["application_id"]),
        document_type=DocumentType(doc["document_type"]),
        safe_filename=doc.get("safe_filename", "document"),
        file_size=int(doc.get("file_size", 0)),
        mime_type=doc.get("mime_type", "application/octet-stream"),
        validation_status=ValidationStatus(doc.get("validation_status", "pending")),
        created_at=doc["created_at"],
    )


async def _read_with_limit(file: UploadFile, max_bytes: int) -> bytes:
    """Read an upload fully while enforcing the size limit early."""
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(_READ_CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise FileValidationError(
                "File is too large. Maximum allowed size is 5 MB.",
                status_code=413,
            )
        chunks.append(chunk)
    await file.close()
    return b"".join(chunks)


async def upload_document(
    db: AsyncDatabase,
    storage: StorageAdapter,
    user: UserContext,
    application_id: str,
    document_type: DocumentType,
    file: UploadFile,
) -> DocumentOut:
    """Validate, store and register one uploaded document."""
    from app.config import get_settings

    application = await application_service.get_owned_application(
        db, user["id"], application_id
    )
    if application.get("status") == "cancelled":
        raise AppError("This application has been cancelled.", status_code=409)

    settings = get_settings()
    try:
        data = await _read_with_limit(file, settings.max_file_size_bytes)
        validated = validate_upload(data, file.content_type, settings.max_file_size_bytes)
    except FileValidationError as exc:
        raise AppError(exc.message, status_code=exc.status_code) from exc

    storage_key = f"{application_id}/{secrets.token_hex(16)}{validated.extension}"
    await storage.save(storage_key, data)

    now = datetime.now(timezone.utc)
    original_name = safe_filename(
        file.filename or f"{document_type.value}{validated.extension}",
        fallback=f"{document_type.value}{validated.extension}",
    )
    record: dict[str, Any] = {
        "application_id": application_id,
        "user_id": user["id"],
        "document_type": document_type.value,
        "storage_key": storage_key,
        "safe_filename": original_name,
        "file_hash": validated.sha256,
        "file_size": validated.size,
        "mime_type": validated.mime_type,
        "validation_status": ValidationStatus.VALIDATED.value,
        "created_at": now,
        "updated_at": now,
    }

    try:
        result = await db[DOCUMENTS].insert_one(record)
    except Exception as exc:
        await storage.delete(storage_key)
        raise AppError("Could not save the uploaded document.", status_code=500) from exc

    new_version = int(application.get("data_version", 1)) + 1
    await db[APPLICATIONS].update_one(
        {"_id": application["_id"]},
        {"$set": {"data_version": new_version, "updated_at": now}},
    )
    await consent_service.revoke_for_change(
        db,
        application_id=application_id,
        user_id=user["id"],
        reason="document_changed",
        data_version=new_version,
    )
    await application_service.refresh_application_state(db, application_id)
    await audit_service.record(
        db,
        action="document.upload",
        actor_type="user",
        actor_id=user["id"],
        user_id=user["id"],
        application_id=application_id,
        message=f"Uploaded {document_type.value}",
        metadata={
            "document_type": document_type.value,
            "mime_type": validated.mime_type,
            "file_size": validated.size,
            "file_hash": validated.sha256,
            "validation_status": ValidationStatus.VALIDATED.value,
        },
    )
    record["_id"] = result.inserted_id
    return serialize_document(record)


async def list_documents(
    db: AsyncDatabase, user: UserContext, application_id: str
) -> list[DocumentOut]:
    """List documents of an application owned by the current user."""
    await application_service.get_owned_application(db, user["id"], application_id)
    cursor = db[DOCUMENTS].find({"application_id": application_id}).sort("created_at", 1)
    return [serialize_document(doc) async for doc in cursor]


async def _get_owned_document(
    db: AsyncDatabase, user: UserContext, document_id: str
) -> dict[str, Any]:
    if not ObjectId.is_valid(document_id):
        raise NotFoundError("Document not found.")
    doc = await db[DOCUMENTS].find_one(
        {"_id": ObjectId(document_id), "user_id": user["id"]}
    )
    if doc is None:
        raise NotFoundError("Document not found.")
    return doc


async def download_document(
    db: AsyncDatabase,
    storage: StorageAdapter,
    user: UserContext,
    document_id: str,
) -> tuple[bytes, str, str]:
    """Return (bytes, mime_type, safe_filename) for a private download."""
    doc = await _get_owned_document(db, user, document_id)
    try:
        data = await storage.read(doc["storage_key"])
    except StorageError as exc:
        raise AppError("The stored file is no longer available.", status_code=404) from exc

    await audit_service.record(
        db,
        action="document.download",
        actor_type="user",
        actor_id=user["id"],
        user_id=user["id"],
        application_id=str(doc["application_id"]),
        message="Document downloaded by owner",
        metadata={
            "document_id": document_id,
            "document_type": doc.get("document_type", ""),
        },
    )
    return data, doc.get("mime_type", "application/octet-stream"), doc.get(
        "safe_filename", "document"
    )


async def delete_document(
    db: AsyncDatabase,
    storage: StorageAdapter,
    user: UserContext,
    document_id: str,
) -> dict[str, str]:
    """Delete a document from storage and MongoDB."""
    doc = await _get_owned_document(db, user, document_id)
    try:
        await storage.delete(doc["storage_key"])
    except StorageError as exc:
        raise AppError("Could not delete the stored file.", status_code=500) from exc

    await db[DOCUMENTS].delete_one({"_id": doc["_id"], "user_id": user["id"]})
    application = await db[APPLICATIONS].find_one(
        {"_id": ObjectId(str(doc["application_id"]))}
    )
    if application is not None:
        new_version = int(application.get("data_version", 1)) + 1
        await db[APPLICATIONS].update_one(
            {"_id": application["_id"]},
            {
                "$set": {
                    "data_version": new_version,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        await consent_service.revoke_for_change(
            db,
            application_id=str(doc["application_id"]),
            user_id=user["id"],
            reason="document_changed",
            data_version=new_version,
        )
    await application_service.refresh_application_state(
        db, str(doc["application_id"])
    )
    await audit_service.record(
        db,
        action="document.delete",
        actor_type="user",
        actor_id=user["id"],
        user_id=user["id"],
        application_id=str(doc["application_id"]),
        message="Document deleted by owner",
        metadata={
            "document_id": document_id,
            "document_type": doc.get("document_type", ""),
        },
    )
    return {"message": "Document deleted."}
