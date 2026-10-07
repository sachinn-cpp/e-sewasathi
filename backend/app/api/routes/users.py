"""User profile routes."""

from __future__ import annotations

from fastapi import APIRouter

from app.dependencies import CurrentUser, DbDep
from app.schemas.user import UserPublic, UserUpdate
from app.services import auth_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserPublic, summary="Read the current user profile")
async def read_profile(current_user: CurrentUser, db: DbDep) -> UserPublic:
    user_doc = await auth_service.get_user_by_id(db, current_user["id"])
    return auth_service.serialize_user(user_doc)


@router.patch("/me", response_model=UserPublic, summary="Update the current user profile")
async def update_profile(
    payload: UserUpdate, current_user: CurrentUser, db: DbDep
) -> UserPublic:
    return await auth_service.update_user(db, current_user["id"], payload)
