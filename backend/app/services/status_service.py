"""Status service: authoritative status changes, timeline and portal polling."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase

from app.database.collections import (
    APPLICATIONS,
    AUDIT_LOGS,
    STATUS_EVENTS,
    WORKFLOWS,
)
from app.errors import NotFoundError
from app.schemas.application import IncomeCertificateFormData
from app.schemas.status import (
    ApplicationStatusOut,
    StatusEventOut,
    StatusSource,
    StatusTimelineOut,
)
from app.schemas.user import UserContext
from app.services import application_service, audit_service, realtime_service
from app.utils.status_mapping import (
    PHASE2_STATUSES,
    PROGRESS_BY_STATUS,
    STEP_BY_STATUS,
    map_portal_status,
    status_message,
)

logger = logging.getLogger(__name__)


async def set_status(
    db: AsyncDatabase,
    application_id: str,
    to_status: str,
    *,
    source: str = StatusSource.WORKFLOW.value,
    language: str = "en",
    actor_id: str | None = None,
    actor_type: str = "system",
    message: str = "",
    metadata: dict[str, Any] | None = None,
    application: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Move an application to a new status and record the timeline event."""
    if application is None:
        if not ObjectId.is_valid(application_id):
            raise NotFoundError("Application not found.")
        application = await db[APPLICATIONS].find_one(
            {"_id": ObjectId(application_id)}
        )
    if application is None:
        raise NotFoundError("Application not found.")

    from_status = str(application.get("status", "draft"))
    now = datetime.now(timezone.utc)

    if to_status in PHASE2_STATUSES:
        step = STEP_BY_STATUS[to_status]
        progress = PROGRESS_BY_STATUS[to_status]
    else:
        form = IncomeCertificateFormData.model_validate(
            application.get("form_data") or {}
        )
        count = await application_service.count_documents(db, application_id)
        step, progress = application_service.compute_step_and_progress(
            to_status, form, count
        )

    updates: dict[str, Any] = {
        "status": to_status,
        "current_step": step,
        "progress_percent": progress,
        "updated_at": now,
    }
    if source == StatusSource.PORTAL.value and metadata:
        updates["portal_status"] = str(metadata.get("portal_status", ""))
    updated = await db[APPLICATIONS].find_one_and_update(
        {"_id": application["_id"]},
        {"$set": updates},
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        raise NotFoundError("Application not found.")

    if to_status != from_status:
        event = {
            "application_id": application_id,
            "from_status": from_status,
            "to_status": to_status,
            "source": source,
            "message": message or status_message(to_status, language),
            "language": language,
            "metadata": metadata or {},
            "created_at": now,
        }
        await db[STATUS_EVENTS].insert_one(dict(event))
        await audit_service.record(
            db,
            action="application.status_changed",
            actor_type=actor_type if actor_type in ("user", "system", "human_helper", "admin") else "system",
            actor_id=actor_id,
            user_id=str(application.get("user_id", "")),
            application_id=application_id,
            message=message or f"Status changed to {to_status}",
            metadata={
                "previous_status": from_status,
                "status": to_status,
                "source": source,
                **(metadata or {}),
            },
        )
        await realtime_service.publish_event(
            application_id,
            {
                "type": "status_changed",
                "from_status": from_status,
                "to_status": to_status,
                "source": source,
                "message": event["message"],
                "progress_percent": progress,
                "current_step": step,
            },
        )
    return updated


async def _load_owned(
    db: AsyncDatabase, user: UserContext, application_id: str
) -> dict[str, Any]:
    app = await application_service.get_owned_application(
        db, user["id"], application_id
    )
    return app


async def refresh_portal_status(
    db: AsyncDatabase, application_id: str, *, actor_id: str | None = None
) -> str | None:
    """Poll the portal for a submitted application and apply changes."""
    from app.integrations import providers

    if not ObjectId.is_valid(application_id):
        return None
    app = await db[APPLICATIONS].find_one({"_id": ObjectId(application_id)})
    if app is None:
        return None
    reference = str(app.get("portal_reference", ""))
    current = str(app.get("status", ""))
    pollable = {"submitted", "under_government_review", "action_required"}
    if not reference or current not in pollable:
        return current

    client = providers.get_portal_client()
    try:
        result = await client.get_application_status(reference)
    finally:
        await client.close()

    await audit_service.record(
        db,
        action="portal.status_checked",
        actor_type="user" if actor_id else "system",
        actor_id=actor_id,
        user_id=str(app.get("user_id", "")),
        application_id=application_id,
        message="Portal status checked",
        result="success" if result.found and not result.lookup_error else "failure",
        metadata={
            "portal_status": result.status,
            "found": result.found,
            "lookup_error": result.lookup_error,
        },
    )

    if not result.found or not result.status:
        return current

    mapped = map_portal_status(result.status)
    language = str(app.get("preferred_language", "en"))
    await set_status(
        db,
        application_id,
        mapped,
        source=StatusSource.PORTAL.value,
        language=language,
        actor_type="system",
        message=status_message(mapped, language),
        metadata={"portal_status": result.status, "portal_reference": reference},
        application=app,
    )
    return mapped


async def status_snapshot(
    db: AsyncDatabase, user: UserContext, application_id: str, *, live: bool = True
) -> ApplicationStatusOut:
    """Current status for the owner, with a live portal poll when possible."""
    app = await _load_owned(db, user, application_id)
    language = user.get("preferred_language", "en") or "en"
    if live:
        await refresh_portal_status(db, application_id, actor_id=user["id"])
        app = await _load_owned(db, user, application_id)

    workflow_status = ""
    workflow = await db[WORKFLOWS].find_one({"application_id": application_id})
    if workflow is not None:
        workflow_status = str(workflow.get("status", ""))

    pending_action = ""
    if workflow is not None and workflow.get("pending_interrupt"):
        pending_action = str(
            (workflow.get("pending_interrupt") or {}).get("name", "")
        )

    status = str(app.get("status", "draft"))
    return ApplicationStatusOut(
        application_id=application_id,
        status=status,
        status_message=status_message(status, language),
        current_step=str(app.get("current_step", "form")),
        progress_percent=int(app.get("progress_percent", 0)),
        portal_status=str(app.get("portal_status", "")),
        portal_reference=str(app.get("portal_reference", "")),
        application_number=str(app.get("application_number", "")),
        pending_action=pending_action,
        workflow_status=workflow_status,
        updated_at=app.get("updated_at", datetime.now(timezone.utc)),
    )


async def timeline(
    db: AsyncDatabase, user: UserContext, application_id: str
) -> StatusTimelineOut:
    """Ordered status events for the owner's application."""
    await _load_owned(db, user, application_id)
    cursor = db[STATUS_EVENTS].find({"application_id": application_id}).sort(
        "created_at", 1
    )
    events: list[StatusEventOut] = []
    async for doc in cursor:
        events.append(
            StatusEventOut(
                id=str(doc["_id"]),
                application_id=str(doc["application_id"]),
                from_status=str(doc.get("from_status", "")),
                to_status=str(doc.get("to_status", "")),
                source=str(doc.get("source", "system")),
                message=str(doc.get("message", "")),
                language=str(doc.get("language", "en")),
                created_at=doc["created_at"],
            )
        )
    return StatusTimelineOut(application_id=application_id, events=events)


async def audit_timeline(
    db: AsyncDatabase, user: UserContext, application_id: str, limit: int = 100
) -> list[dict[str, Any]]:
    """Audit events for an application, visible to its owner."""
    await _load_owned(db, user, application_id)
    cursor = (
        db[AUDIT_LOGS]
        .find({"application_id": application_id})
        .sort("created_at", -1)
        .limit(limit)
    )
    return [
        {
            "id": str(doc["_id"]),
            "action": str(doc.get("action", "")),
            "actor_type": str(doc.get("actor_type", "")),
            "message": str(doc.get("message", "")),
            "result": str(doc.get("result", "success")),
            "metadata": doc.get("metadata", {}),
            "created_at": doc["created_at"],
        }
        async for doc in cursor
    ]


async def notify_status_change(
    db: AsyncDatabase,
    application_id: str,
    *,
    kind: str,
    title: str,
    body: str = "",
    language: str = "en",
    user_id: str = "",
) -> None:
    """Convenience wrapper used by the workflow for citizen notifications."""
    from app.services import notification_service

    if not user_id:
        if not ObjectId.is_valid(application_id):
            return
        app = await db[APPLICATIONS].find_one({"_id": ObjectId(application_id)})
        if app is None:
            return
        user_id = str(app.get("user_id", ""))
    if not user_id:
        return
    await notification_service.notify(
        db,
        user_id=user_id,
        application_id=application_id,
        kind=kind,
        title=title,
        body=body,
        language=language,
    )
