"""Authentication routes."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.dependencies import CurrentUser, DbDep
from app.schemas.auth import LoginRequest, MessageResponse, RegisterRequest, TokenResponse
from app.schemas.user import UserPublic
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new citizen account",
)
async def register(payload: RegisterRequest, db: DbDep) -> UserPublic:
    return await auth_service.register(db, payload)


@router.post("/login", response_model=TokenResponse, summary="Sign in and receive a JWT")
async def login(payload: LoginRequest, db: DbDep) -> TokenResponse:
    return await auth_service.login(db, payload)


@router.get("/me", response_model=UserPublic, summary="Current authenticated user")
async def me(current_user: CurrentUser, db: DbDep) -> UserPublic:
    user_doc = await auth_service.get_user_by_id(db, current_user["id"])
    return auth_service.serialize_user(user_doc)


@router.post("/logout", response_model=MessageResponse, summary="Record a sign out")
async def logout(current_user: CurrentUser, db: DbDep) -> MessageResponse:
    await auth_service.record_logout(db, current_user["id"], current_user["email"])
    return MessageResponse(message="Signed out successfully.")
