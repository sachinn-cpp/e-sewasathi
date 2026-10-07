"""Consent schemas for Phase 2."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ConsentAction(str, Enum):
    """Sensitive actions that require explicit, backend-verified consent."""

    READ_UPLOADED_DOCUMENT = "read_uploaded_document"
    EXTRACT_DOCUMENT_INFORMATION = "extract_document_information"
    FILL_APPLICATION_FORM = "fill_application_form"
    SHARE_DATA_WITH_PORTAL = "share_data_with_portal"
    SUBMIT_APPLICATION = "submit_application"
    TRACK_APPLICATION_STATUS = "track_application_status"
    ESCALATE_TO_HUMAN = "escalate_to_human"


class ConsentState(str, Enum):
    GRANTED = "granted"
    DENIED = "denied"
    REVOKED = "revoked"


class ConsentCreate(BaseModel):
    """Payload for POST /api/applications/{application_id}/consents."""

    action: ConsentAction
    approved: bool
    language: str = Field(default="en", max_length=10)


class ConsentOut(BaseModel):
    """Public representation of one consent record."""

    id: str
    application_id: str
    user_id: str
    action: ConsentAction
    state: ConsentState
    data_version: int
    language: str = "en"
    created_at: datetime
    updated_at: datetime
    valid: bool = False


class ConsentStatusOut(BaseModel):
    """Consent summary for an application at its current data_version."""

    application_id: str
    data_version: int
    consents: list[ConsentOut]
    missing_actions: list[ConsentAction]
