"""Chat and status tracking schemas for Phase 2."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ChatSendRequest(BaseModel):
    """Payload for POST /api/applications/{application_id}/chat."""

    message: str = Field(min_length=1, max_length=4000)
    language: str = Field(default="", max_length=10)


class ChatMessageOut(BaseModel):
    """One stored chat message."""

    id: str
    application_id: str
    role: str
    message: str
    language: str
    created_at: datetime


class ChatHistoryOut(BaseModel):
    """Chat history for an application."""

    application_id: str
    messages: list[ChatMessageOut]


class ApplicationStatusOut(BaseModel):
    """Current status snapshot of an application."""

    application_id: str
    status: str
    status_message: str
    current_step: str
    progress_percent: int
    portal_status: str = ""
    portal_reference: str = ""
    application_number: str
    pending_action: str = ""
    workflow_status: str = ""
    updated_at: datetime


class StatusEventOut(BaseModel):
    """One timeline event."""

    id: str
    application_id: str
    from_status: str
    to_status: str
    source: str
    message: str
    language: str = "en"
    created_at: datetime


class StatusTimelineOut(BaseModel):
    """Timeline of status events for an application."""

    application_id: str
    events: list[StatusEventOut]


class StatusSource(str, Enum):
    USER = "user"
    WORKFLOW = "workflow"
    PORTAL = "portal"
    SYSTEM = "system"
