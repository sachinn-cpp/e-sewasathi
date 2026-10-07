"""Application routes."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.dependencies import CurrentUser, DbDep
from app.schemas.application import ApplicationCreate, ApplicationOut, ApplicationUpdate
from app.services import application_service

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post(
    "",
    response_model=ApplicationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create an application",
)
async def create_application(
    payload: ApplicationCreate, current_user: CurrentUser, db: DbDep
) -> ApplicationOut:
    return await application_service.create_application(db, current_user, payload)


@router.get("", response_model=list[ApplicationOut], summary="List my applications")
async def list_applications(current_user: CurrentUser, db: DbDep) -> list[ApplicationOut]:
    return await application_service.list_applications(db, current_user)


@router.get("/{application_id}", response_model=ApplicationOut, summary="Get an application")
async def get_application(
    application_id: str, current_user: CurrentUser, db: DbDep
) -> ApplicationOut:
    return await application_service.get_application(db, current_user, application_id)


@router.patch("/{application_id}", response_model=ApplicationOut, summary="Update an application")
async def update_application(
    application_id: str,
    payload: ApplicationUpdate,
    current_user: CurrentUser,
    db: DbDep,
) -> ApplicationOut:
    return await application_service.update_application(
        db, current_user, application_id, payload
    )


@router.delete(
    "/{application_id}",
    response_model=ApplicationOut,
    summary="Cancel an application",
)
async def cancel_application(
    application_id: str, current_user: CurrentUser, db: DbDep
) -> ApplicationOut:
    return await application_service.cancel_application(db, current_user, application_id)
