"""Consent service: backend-verified, data-version bound consent records."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase

from app.database.collections import APPLICATIONS, CONSENTS
from app.errors import AppError, NotFoundError
from app.schemas.consent import (
    ConsentAction,
    ConsentOut,
    ConsentState,
    ConsentStatusOut,
)
from app.schemas.user import UserContext
from app.services import audit_service
from app.utils.error_codes import CONSENT_REQUIRED, message_for

logger = logging.getLogger(__name__)


def _serialize(doc: dict[str, Any], data_version: int) -> ConsentOut:
    state = ConsentState(doc.get("state", ConsentState.REVOKED.value))
    return ConsentOut(
        id=str(doc["_id"]),
        application_id=str(doc["application_id"]),
        user_id=str(doc["user_id"]),
        action=ConsentAction(doc["action"]),
        state=state,
        data_version=int(doc.get("data_version", 1)),
        language=doc.get("language", "en"),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
        valid=state is ConsentState.GRANTED
        and int(doc.get("data_version", 1)) == data_version,
    )


async def _get_application(
    db: AsyncDatabase, user_id: str | None, application_id: str
) -> dict[str, Any]:
    if not ObjectId.is_valid(application_id):
        raise NotFoundError("Application not found.")
    query: dict[str, Any] = {"_id": ObjectId(application_id)}
    if user_id is not None:
        query["user_id"] = user_id
    doc = await db[APPLICATIONS].find_one(query)
    if doc is None:
        raise NotFoundError("Application not found.")
    return doc


async def _upsert(
    db: AsyncDatabase,
    *,
    user: UserContext,
    application_id: str,
    action: ConsentAction,
    state: ConsentState,
    data_version: int,
    language: str,
) -> ConsentOut:
    now = datetime.now(timezone.utc)
    await db[CONSENTS].update_one(
        {"application_id": application_id, "user_id": user["id"], "action": action.value},
        {
            "$set": {
                "state": state.value,
                "data_version": data_version,
                "language": language,
                "updated_at": now,
            },
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )
    doc = await db[CONSENTS].find_one(
        {"application_id": application_id, "user_id": user["id"], "action": action.value}
    )
    if doc is None:  # pragma: no cover - upsert just happened
        raise AppError("Could not save consent.", status_code=500)
    return _serialize(doc, data_version)


async def grant(
    db: AsyncDatabase,
    user: UserContext,
    application_id: str,
    action: ConsentAction,
    language: str = "en",
) -> ConsentOut:
    """Record an explicit approval for one action at the current data version."""
    application = await _get_application(db, user["id"], application_id)
    data_version = int(application.get("data_version", 1))
    consent = await _upsert(
        db,
        user=user,
        application_id=application_id,
        action=action,
        state=ConsentState.GRANTED,
        data_version=data_version,
        language=language,
    )
    await audit_service.record(
        db,
        action="consent.granted",
        actor_type="user",
        actor_id=user["id"],
        user_id=user["id"],
        application_id=application_id,
        message=f"Consent granted: {action.value}",
        metadata={"action": action.value, "data_version": data_version},
    )
    return consent


async def deny(
    db: AsyncDatabase,
    user: UserContext,
    application_id: str,
    action: ConsentAction,
    language: str = "en",
) -> ConsentOut:
    """Record an explicit refusal for one action."""
    application = await _get_application(db, user["id"], application_id)
    data_version = int(application.get("data_version", 1))
    consent = await _upsert(
        db,
        user=user,
        application_id=application_id,
        action=action,
        state=ConsentState.DENIED,
        data_version=data_version,
        language=language,
    )
    await audit_service.record(
        db,
        action="consent.denied",
        actor_type="user",
        actor_id=user["id"],
        user_id=user["id"],
        application_id=application_id,
        message=f"Consent denied: {action.value}",
        metadata={"action": action.value, "data_version": data_version},
    )
    return consent


async def revoke(
    db: AsyncDatabase,
    user: UserContext,
    application_id: str,
    action: ConsentAction,
) -> ConsentOut | None:
    """Revoke one previously granted consent."""
    application = await _get_application(db, user["id"], application_id)
    data_version = int(application.get("data_version", 1))
    doc = await db[CONSENTS].find_one(
        {"application_id": application_id, "user_id": user["id"], "action": action.value}
    )
    if doc is None:
        return None
    now = datetime.now(timezone.utc)
    await db[CONSENTS].update_one(
        {"_id": doc["_id"]},
        {"$set": {"state": ConsentState.REVOKED.value, "updated_at": now}},
    )
    doc["state"] = ConsentState.REVOKED.value
    doc["updated_at"] = now
    await audit_service.record(
        db,
        action="consent.revoked",
        actor_type="user",
        actor_id=user["id"],
        user_id=user["id"],
        application_id=application_id,
        message=f"Consent revoked: {action.value}",
        metadata={"action": action.value, "data_version": data_version},
    )
    return _serialize(doc, data_version)


async def revoke_for_change(
    db: AsyncDatabase,
    *,
    application_id: str,
    user_id: str,
    reason: str,
    data_version: int,
) -> int:
    """Revoke every granted consent because the application data changed."""
    now = datetime.now(timezone.utc)
    result = await db[CONSENTS].update_many(
        {
            "application_id": application_id,
            "state": ConsentState.GRANTED.value,
        },
        {
            "$set": {
                "state": ConsentState.REVOKED.value,
                "updated_at": now,
                "revoked_by": reason,
            }
        },
    )
    if result.modified_count:
        await audit_service.record(
            db,
            action="consent.revoked",
            actor_type="system",
            actor_id=None,
            user_id=user_id,
            application_id=application_id,
            message=f"Consents revoked after {reason}",
            metadata={
                "reason": reason,
                "data_version": data_version,
                "revoked_count": result.modified_count,
            },
        )
    return int(result.modified_count)


async def has_valid_grant(
    db: AsyncDatabase,
    *,
    user_id: str,
    application_id: str,
    action: ConsentAction,
    data_version: int,
) -> bool:
    """True only when a grant exists for exactly the current data version."""
    doc = await db[CONSENTS].find_one(
        {
            "application_id": application_id,
            "user_id": user_id,
            "action": action.value,
            "state": ConsentState.GRANTED.value,
            "data_version": data_version,
        }
    )
    return doc is not None


async def has_denial(
    db: AsyncDatabase,
    *,
    user_id: str,
    application_id: str,
    action: ConsentAction,
    data_version: int,
) -> bool:
    doc = await db[CONSENTS].find_one(
        {
            "application_id": application_id,
            "user_id": user_id,
            "action": action.value,
            "state": ConsentState.DENIED.value,
            "data_version": data_version,
        }
    )
    return doc is not None


async def assert_granted(
    db: AsyncDatabase,
    *,
    user_id: str,
    application_id: str,
    action: ConsentAction,
    data_version: int,
) -> None:
    """Raise ConsentRequiredError unless backend-verified consent exists."""
    if not await has_valid_grant(
        db,
        user_id=user_id,
        application_id=application_id,
        action=action,
        data_version=data_version,
    ):
        raise ConsentRequiredError(
            details={"action": action.value, "data_version": data_version}
        )


async def list_for_application(
    db: AsyncDatabase, user: UserContext, application_id: str
) -> list[ConsentOut]:
    application = await _get_application(db, user["id"], application_id)
    data_version = int(application.get("data_version", 1))
    cursor = db[CONSENTS].find(
        {"application_id": application_id, "user_id": user["id"]}
    ).sort("action", 1)
    return [_serialize(doc, data_version) async for doc in cursor]


async def status_snapshot(
    db: AsyncDatabase, user: UserContext, application_id: str
) -> ConsentStatusOut:
    application = await _get_application(db, user["id"], application_id)
    data_version = int(application.get("data_version", 1))
    consents = await list_for_application(db, user, application_id)
    granted = {c.action for c in consents if c.valid}
    required_for_submission = [
        ConsentAction.SHARE_DATA_WITH_PORTAL,
        ConsentAction.SUBMIT_APPLICATION,
    ]
    missing = [a for a in required_for_submission if a not in granted]
    return ConsentStatusOut(
        application_id=application_id,
        data_version=data_version,
        consents=consents,
        missing_actions=missing,
    )


async def require_message(db: AsyncDatabase, application_id: str) -> str:
    """Human readable reason used when consent is missing (logged, not raised)."""
    return message_for(CONSENT_REQUIRED)


async def ensure_all_granted(
    db: AsyncDatabase,
    *,
    user_id: str,
    application_id: str,
    data_version: int,
    actions: tuple[ConsentAction, ...],
) -> None:
    """Raise ConsentRequiredError unless every required action is granted."""
    for action in actions:
        await assert_granted(
            db,
            user_id=user_id,
            application_id=application_id,
            action=action,
            data_version=data_version,
        )
