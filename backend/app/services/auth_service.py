"""Authentication service: registration, login, profile reads."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from app.database.collections import USERS
from app.errors import ConflictError, NotFoundError, UnauthorizedError
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserPublic, UserUpdate
from app.services import audit_service
from app.utils.hashing import hash_password, verify_password
from app.utils.pii_masking import mask_email
from app.utils.security import create_access_token
from app.utils.validators import normalize_email

# Verified against when an account does not exist so that the response time
# of a missing account matches the response time of a wrong password.
_DUMMY_PASSWORD_HASH: str | None = None


def _dummy_hash() -> str:
    global _DUMMY_PASSWORD_HASH
    if _DUMMY_PASSWORD_HASH is None:
        _DUMMY_PASSWORD_HASH = hash_password("dummy-password-placeholder-000")
    return _DUMMY_PASSWORD_HASH


def serialize_user(doc: Mapping[str, Any]) -> UserPublic:
    """Convert a raw user document into the public schema."""
    return UserPublic(
        id=str(doc["_id"]),
        name=doc["name"],
        email=doc["email"],
        phone=doc.get("phone", ""),
        role=doc.get("role", "citizen"),
        preferred_language=doc.get("preferred_language", "en"),
        created_at=doc["created_at"],
    )


async def register(db: AsyncDatabase, payload: RegisterRequest) -> UserPublic:
    """Create a new citizen account."""
    email = normalize_email(payload.email)
    existing = await db[USERS].find_one({"email": email})
    if existing is not None:
        raise ConflictError("An account with this email already exists.")

    now = datetime.now(timezone.utc)
    record: dict[str, Any] = {
        "name": payload.name.strip(),
        "email": email,
        "phone": payload.phone.strip(),
        "password_hash": hash_password(payload.password),
        "role": "citizen",
        "preferred_language": payload.preferred_language,
        "created_at": now,
        "updated_at": now,
    }
    try:
        result = await db[USERS].insert_one(record)
    except DuplicateKeyError as exc:
        raise ConflictError("An account with this email already exists.") from exc

    user_id = str(result.inserted_id)
    await audit_service.record(
        db,
        action="user.register",
        actor_type="user",
        actor_id=user_id,
        user_id=user_id,
        message="User registered",
        metadata={"email": email},
    )
    record["_id"] = result.inserted_id
    return serialize_user(record)


async def login(db: AsyncDatabase, payload: LoginRequest) -> TokenResponse:
    """Verify credentials and issue a JWT."""
    email = normalize_email(payload.email)
    user = await db[USERS].find_one({"email": email})

    if user is None:
        verify_password(payload.password, _dummy_hash())
        await audit_service.record(
            db,
            action="user.login",
            actor_type="system",
            actor_id=None,
            result="failure",
            message="Login failed for unknown account",
            metadata={"email": email},
        )
        raise UnauthorizedError("Invalid email or password.")

    if not verify_password(payload.password, user.get("password_hash", "")):
        await audit_service.record(
            db,
            action="user.login",
            actor_type="user",
            actor_id=str(user["_id"]),
            user_id=str(user["_id"]),
            result="failure",
            message="Login failed: incorrect password",
            metadata={"email": email},
        )
        raise UnauthorizedError("Invalid email or password.")

    user_id = str(user["_id"])
    token = create_access_token(user_id, user.get("role", "citizen"))
    await audit_service.record(
        db,
        action="user.login",
        actor_type="user",
        actor_id=user_id,
        user_id=user_id,
        message="User signed in",
        metadata={"email": email},
    )
    return TokenResponse(access_token=token, user=serialize_user(user))


async def get_user_by_id(db: AsyncDatabase, user_id: str) -> dict[str, Any]:
    """Fetch a user document by id or raise NotFoundError."""
    if not ObjectId.is_valid(user_id):
        raise NotFoundError("User not found.")
    doc = await db[USERS].find_one({"_id": ObjectId(user_id)})
    if doc is None:
        raise NotFoundError("User not found.")
    return doc


async def update_user(
    db: AsyncDatabase, user_id: str, payload: UserUpdate
) -> UserPublic:
    """Update the editable profile fields of the current user."""
    updates: dict[str, Any] = {}
    if payload.preferred_language is not None:
        updates["preferred_language"] = payload.preferred_language
    if payload.name is not None:
        updates["name"] = payload.name.strip()
    if not updates:
        doc = await get_user_by_id(db, user_id)
        return serialize_user(doc)

    updates["updated_at"] = datetime.now(timezone.utc)
    doc = await db[USERS].find_one_and_update(
        {"_id": ObjectId(user_id)},
        {"$set": updates},
        return_document=ReturnDocument.AFTER,
    )
    if doc is None:
        raise NotFoundError("User not found.")
    return serialize_user(doc)


async def record_logout(db: AsyncDatabase, user_id: str, email: str) -> None:
    """Write an audit event for a sign out."""
    await audit_service.record(
        db,
        action="user.logout",
        actor_type="user",
        actor_id=user_id,
        user_id=user_id,
        message="User signed out",
        metadata={"email": mask_email(email)},
    )
