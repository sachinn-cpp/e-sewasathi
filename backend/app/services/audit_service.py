"""Audit log service. Every important state change writes one audit event."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Literal

from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase

from app.database.collections import AUDIT_LOGS
from app.utils.pii_masking import mask_metadata

logger = logging.getLogger(__name__)

ActorType = Literal["user", "system", "human_helper", "admin"]


async def record(
    db: AsyncDatabase,
    *,
    action: str,
    actor_type: ActorType,
    actor_id: str | None,
    result: str = "success",
    message: str = "",
    application_id: str | None = None,
    user_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Write one audit event and return its id.

    Metadata is PII masked before it is persisted, and audit failures never
    break the requesting workflow.
    """
    # Ids are stored as plain strings so audit records can be queried with the
    # same values the API exposes (applications and documents do the same).
    document: dict[str, Any] = {
        "application_id": application_id,
        "user_id": user_id,
        "actor_type": actor_type,
        "actor_id": actor_id,
        "action": action,
        "result": result,
        "message": message,
        "metadata": mask_metadata(metadata or {}),
        "created_at": datetime.now(timezone.utc),
    }
    try:
        result_id = await db[AUDIT_LOGS].insert_one(document)
        return str(result_id.inserted_id)
    except Exception:
        logger.exception("Failed to write audit event '%s'", action)
        return ""
