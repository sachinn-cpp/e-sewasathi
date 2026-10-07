"""Application service: CRUD, ownership checks, progress and audit events."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Mapping

from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase

from app.database.collections import APPLICATIONS, DOCUMENTS
from app.errors import AppError, NotFoundError
from app.schemas.application import (
    ACTIVE_STATUSES,
    ApplicationCreate,
    ApplicationOut,
    ApplicationStatus,
    ApplicationUpdate,
    IncomeCertificateFormData,
    ServiceType,
)
from app.schemas.document import DocumentType
from app.schemas.user import UserContext
from app.services import audit_service
from app.utils.status_mapping import (
    PHASE2_STATUSES,
    PROGRESS_BY_STATUS,
    STEP_BY_STATUS,
)
from app.utils.validators import generate_application_number

logger = logging.getLogger(__name__)

REQUIRED_DOCUMENT_TYPES: tuple[str, ...] = tuple(doc.value for doc in DocumentType)


def serialize_application(doc: Mapping[str, Any], document_count: int = 0) -> ApplicationOut:
    """Convert a raw application document into the public schema."""
    return ApplicationOut(
        id=str(doc["_id"]),
        user_id=str(doc["user_id"]),
        service_type=ServiceType(doc["service_type"]),
        status=ApplicationStatus(doc["status"]),
        current_step=doc.get("current_step", "form"),
        progress_percent=int(doc.get("progress_percent", 0)),
        form_data=IncomeCertificateFormData.model_validate(doc.get("form_data") or {}),
        data_version=int(doc.get("data_version", 1)),
        application_number=doc.get("application_number", ""),
        document_count=document_count,
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


def compute_step_and_progress(
    status: str,
    form_data: IncomeCertificateFormData,
    document_count: int,
) -> tuple[str, int]:
    """Derive the current step and progress percentage from real state."""
    if status == ApplicationStatus.CANCELLED.value:
        return "cancelled", 100
    if status in PHASE2_STATUSES:
        return STEP_BY_STATUS[status], PROGRESS_BY_STATUS[status]

    required = len(REQUIRED_DOCUMENT_TYPES)
    uploaded = min(document_count, required)
    form_complete = form_data.is_complete()

    progress = 40 if form_complete else 0
    progress += round(40 * uploaded / required)

    if form_complete and uploaded == required:
        return "review", 100
    if not form_complete:
        return "form", progress
    return "documents", progress


async def get_owned_application(
    db: AsyncDatabase, user_id: str, application_id: str
) -> dict[str, Any]:
    """Fetch an application only when it belongs to the given user.

    A missing application and another user's application both return 404 so
    that ownership cannot be probed.
    """
    if not ObjectId.is_valid(application_id):
        raise NotFoundError("Application not found.")
    doc = await db[APPLICATIONS].find_one(
        {"_id": ObjectId(application_id), "user_id": user_id}
    )
    if doc is None:
        raise NotFoundError("Application not found.")
    return doc


async def count_documents(db: AsyncDatabase, application_id: str) -> int:
    """Count uploaded documents for an application."""
    return await db[DOCUMENTS].count_documents({"application_id": application_id})


async def _with_document_count(
    db: AsyncDatabase, doc: Mapping[str, Any]
) -> ApplicationOut:
    count = await count_documents(db, str(doc["_id"]))
    return serialize_application(doc, count)


async def create_application(
    db: AsyncDatabase, user: UserContext, payload: ApplicationCreate
) -> ApplicationOut:
    """Create a new income certificate application for the current user."""
    if payload.service_type is not ServiceType.INCOME_CERTIFICATE:
        raise AppError("This service is not available in Phase 1.", status_code=400)

    now = datetime.now(timezone.utc)
    form_data = payload.form_data.model_copy(
        update={"preferred_language": payload.preferred_language}
    )
    step, progress = compute_step_and_progress(
        ApplicationStatus.DRAFT.value, form_data, 0
    )
    record: dict[str, Any] = {
        "user_id": user["id"],
        "service_type": payload.service_type.value,
        "status": ApplicationStatus.DRAFT.value,
        "current_step": step,
        "progress_percent": progress,
        "form_data": form_data.model_dump(),
        "data_version": 1,
        "application_number": generate_application_number(),
        "created_at": now,
        "updated_at": now,
    }
    result = await db[APPLICATIONS].insert_one(record)
    application_id = str(result.inserted_id)

    await audit_service.record(
        db,
        action="application.create",
        actor_type="user",
        actor_id=user["id"],
        user_id=user["id"],
        application_id=application_id,
        message=f"Created {payload.service_type.value} application",
        metadata={"application_number": record["application_number"]},
    )
    record["_id"] = result.inserted_id
    return await _with_document_count(db, record)


async def list_applications(db: AsyncDatabase, user: UserContext) -> list[ApplicationOut]:
    """List only the current user's applications, newest first."""
    cursor = db[APPLICATIONS].find({"user_id": user["id"]}).sort("created_at", -1)
    applications: list[ApplicationOut] = []
    async for doc in cursor:
        applications.append(await _with_document_count(db, doc))
    return applications


async def get_application(
    db: AsyncDatabase, user: UserContext, application_id: str
) -> ApplicationOut:
    """Get one of the current user's applications."""
    doc = await get_owned_application(db, user["id"], application_id)
    return await _with_document_count(db, doc)


async def update_application(
    db: AsyncDatabase,
    user: UserContext,
    application_id: str,
    payload: ApplicationUpdate,
) -> ApplicationOut:
    """Edit form data and/or move the application status."""
    doc = await get_owned_application(db, user["id"], application_id)
    current_status = doc.get("status", ApplicationStatus.DRAFT.value)

    if current_status == ApplicationStatus.CANCELLED.value and payload.status is None:
        raise AppError("A cancelled application can no longer be edited.", status_code=409)
    if current_status == ApplicationStatus.CANCELLED.value:
        raise AppError("A cancelled application cannot be reopened in Phase 1.", status_code=409)

    now = datetime.now(timezone.utc)
    updates: dict[str, Any] = {"updated_at": now}

    if payload.form_data is not None:
        existing_form = IncomeCertificateFormData.model_validate(doc.get("form_data") or {})
        new_form = payload.form_data
        changed_keys = [
            key
            for key in new_form.model_dump()
            if new_form.model_dump().get(key) != existing_form.model_dump().get(key)
        ]
        updates["form_data"] = new_form.model_dump()
        updates["data_version"] = int(doc.get("data_version", 1)) + 1
        from app.services import consent_service

        await consent_service.revoke_for_change(
            db,
            application_id=application_id,
            user_id=user["id"],
            reason="form_updated",
            data_version=updates["data_version"],
        )
        await audit_service.record(
            db,
            action="application.form_updated",
            actor_type="user",
            actor_id=user["id"],
            user_id=user["id"],
            application_id=application_id,
            message="Application form data updated",
            metadata={
                "data_version": updates["data_version"],
                "changed_fields": ", ".join(changed_keys) or "none",
            },
        )

    new_status: str | None = None
    if payload.status is not None:
        if payload.status is ApplicationStatus.CANCELLED:
            new_status = ApplicationStatus.CANCELLED.value
        elif payload.status.value not in {s.value for s in ACTIVE_STATUSES}:
            raise AppError("Unsupported status value.", status_code=400)
        else:
            new_status = payload.status.value
        updates["status"] = new_status

    form_for_progress = IncomeCertificateFormData.model_validate(updates.get("form_data") or doc.get("form_data") or {})
    document_count = await count_documents(db, application_id)
    effective_status = new_status or current_status
    step, progress = compute_step_and_progress(effective_status, form_for_progress, document_count)
    updates["current_step"] = step
    updates["progress_percent"] = progress

    updated = await db[APPLICATIONS].find_one_and_update(
        {"_id": doc["_id"], "user_id": user["id"]},
        {"$set": updates},
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        raise NotFoundError("Application not found.")

    if new_status == ApplicationStatus.CANCELLED.value and current_status != new_status:
        await audit_service.record(
            db,
            action="application.cancel",
            actor_type="user",
            actor_id=user["id"],
            user_id=user["id"],
            application_id=application_id,
            message="Application cancelled by owner",
            metadata={"previous_status": current_status},
        )
    elif new_status is not None and new_status != current_status:
        await audit_service.record(
            db,
            action="application.status_changed",
            actor_type="user",
            actor_id=user["id"],
            user_id=user["id"],
            application_id=application_id,
            message="Application status changed",
            metadata={"previous_status": current_status, "status": new_status},
        )

    return await _with_document_count(db, updated)


async def cancel_application(
    db: AsyncDatabase, user: UserContext, application_id: str
) -> ApplicationOut:
    """Cancel an application (idempotent)."""
    doc = await get_owned_application(db, user["id"], application_id)
    if doc.get("status") == ApplicationStatus.CANCELLED.value:
        return await _with_document_count(db, doc)
    payload = ApplicationUpdate(status=ApplicationStatus.CANCELLED)
    return await update_application(db, user, application_id, payload)


async def refresh_application_state(
    db: AsyncDatabase, application_id: str
) -> dict[str, Any] | None:
    """Recompute status, step and progress after document changes.

    Status transitions handled here:
    - draft -> documents_pending after the first upload
    - documents_pending -> awaiting_user_review when the form is complete
      and every required document is uploaded.
    """
    if not ObjectId.is_valid(application_id):
        return None
    doc = await db[APPLICATIONS].find_one({"_id": ObjectId(application_id)})
    if doc is None:
        return None
    status = doc.get("status", ApplicationStatus.DRAFT.value)
    if status == ApplicationStatus.CANCELLED.value:
        return doc
    if status in PHASE2_STATUSES:
        # Phase 2 workflow statuses are owned by the workflow/status service.
        return doc

    form_data = IncomeCertificateFormData.model_validate(doc.get("form_data") or {})
    document_count = await count_documents(db, application_id)
    step, progress = compute_step_and_progress(status, form_data, document_count)

    new_status = status
    if document_count > 0 and status == ApplicationStatus.DRAFT.value:
        new_status = ApplicationStatus.DOCUMENTS_PENDING.value
    if step == "review" and status != ApplicationStatus.AWAITING_USER_REVIEW.value:
        new_status = ApplicationStatus.AWAITING_USER_REVIEW.value

    updates: dict[str, Any] = {
        "status": new_status,
        "current_step": step,
        "progress_percent": progress,
        "updated_at": datetime.now(timezone.utc),
    }
    updated = await db[APPLICATIONS].find_one_and_update(
        {"_id": doc["_id"]},
        {"$set": updates},
        return_document=ReturnDocument.AFTER,
    )
    if updated is not None and new_status != status:
        await audit_service.record(
            db,
            action="application.status_changed",
            actor_type="system",
            actor_id=None,
            user_id=str(doc["user_id"]),
            application_id=application_id,
            message="Application status updated automatically",
            metadata={"previous_status": status, "status": new_status},
        )
    return updated
