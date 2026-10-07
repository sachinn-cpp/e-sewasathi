"""Notification service: stored in-app notices plus realtime events."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase

from app.database.collections import NOTIFICATIONS
from app.errors import NotFoundError
from app.schemas.user import UserContext
from app.services import realtime_service


def _serialize(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(doc["_id"]),
        "application_id": str(doc.get("application_id", "")),
        "kind": doc.get("kind", "info"),
        "title": doc.get("title", ""),
        "body": doc.get("body", ""),
        "language": doc.get("language", "en"),
        "read": bool(doc.get("read", False)),
        "created_at": doc["created_at"],
    }


async def notify(
    db: AsyncDatabase,
    *,
    user_id: str,
    application_id: str,
    kind: str,
    title: str,
    body: str = "",
    language: str = "en",
) -> dict[str, Any]:
    """Create a notification and push it to live subscribers."""
    document = {
        "user_id": user_id,
        "application_id": application_id,
        "kind": kind,
        "title": title,
        "body": body,
        "language": language,
        "read": False,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db[NOTIFICATIONS].insert_one(document)
    document["_id"] = result.inserted_id
    serialized = _serialize(document)
    await realtime_service.publish_event(
        application_id, {"type": "notification", "notification": serialized}
    )
    return serialized


async def list_notifications(
    db: AsyncDatabase, user: UserContext, limit: int = 50
) -> list[dict[str, Any]]:
    cursor = db[NOTIFICATIONS].find({"user_id": user["id"]}).sort("created_at", -1)
    notifications: list[dict[str, Any]] = []
    async for doc in cursor.limit(limit):
        notifications.append(_serialize(doc))
    return notifications


async def mark_read(
    db: AsyncDatabase, user: UserContext, notification_id: str
) -> dict[str, Any]:
    if not ObjectId.is_valid(notification_id):
        raise NotFoundError("Notification not found.")
    doc = await db[NOTIFICATIONS].find_one_and_update(
        {"_id": ObjectId(notification_id), "user_id": user["id"], "read": False},
        {"$set": {"read": True}},
    )
    if doc is None:
        existing = await db[NOTIFICATIONS].find_one(
            {"_id": ObjectId(notification_id), "user_id": user["id"]}
        )
        if existing is None:
            raise NotFoundError("Notification not found.")
        return _serialize(existing)
    doc["read"] = True
    return _serialize(doc)
