"""Shared FastAPI dependencies: database, storage and JWT authentication."""

from __future__ import annotations

from typing import Annotated, Awaitable, Callable

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from pymongo.asynchronous.database import AsyncDatabase

from app.config import Settings, get_settings
from app.database.mongodb import get_database
from app.errors import ForbiddenError, UnauthorizedError
from app.integrations.storage.base import StorageAdapter
from app.integrations.storage.local_storage import LocalStorage
from app.schemas.user import UserContext
from app.utils.security import TokenError, decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_storage_dep() -> StorageAdapter:
    """Build the private storage adapter from settings."""
    return LocalStorage(get_settings().upload_dir)


def get_settings_dep() -> Settings:
    return get_settings()


async def get_db() -> AsyncDatabase:
    return get_database()


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncDatabase, Depends(get_db)],
) -> UserContext:
    """Resolve the authenticated user from the JWT. Never from request bodies."""
    try:
        payload = decode_access_token(token)
    except TokenError as exc:
        raise UnauthorizedError(str(exc)) from exc

    from bson import ObjectId

    from app.database.collections import USERS

    user_id: str = str(payload["sub"])
    if not ObjectId.is_valid(user_id):
        raise UnauthorizedError("Invalid authentication token.")
    user = await db[USERS].find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise UnauthorizedError("Invalid authentication token.")

    return UserContext(
        id=str(user["_id"]),
        name=user.get("name", ""),
        email=user.get("email", ""),
        role=user.get("role", "citizen"),
        preferred_language=user.get("preferred_language", "en"),
    )


def require_roles(*roles: str) -> Callable[..., Awaitable[UserContext]]:
    """Dependency factory that restricts a route to specific roles."""

    async def checker(
        user: Annotated[UserContext, Depends(get_current_user)],
    ) -> UserContext:
        if user["role"] not in roles:
            raise ForbiddenError("You do not have permission to perform this action.")
        return user

    return checker


DbDep = Annotated[AsyncDatabase, Depends(get_db)]
StorageDep = Annotated[StorageAdapter, Depends(get_storage_dep)]
CurrentUser = Annotated[UserContext, Depends(get_current_user)]
SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
