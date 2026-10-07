"""Escalation schemas for human-helper workflows."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class EscalationStatus(str, Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    RESOLVED = "resolved"


class EscalationCreate(BaseModel):
    """Payload used internally when the workflow escalates."""

    reason_code: str
    reason: str
    return_node: str = ""


class EscalationOut(BaseModel):
    """Public representation of an escalation."""

    id: str
    application_id: str
    user_reference: str
    reason_code: str
    reason: str
    status: EscalationStatus
    assigned_helper_id: str = ""
    assigned_helper_name: str = ""
    helper_note: str = ""
    language: str = "en"
    created_at: datetime
    updated_at: datetime


class EscalationResolveRequest(BaseModel):
    """Payload for POST /api/helper/escalations/{escalation_id}/resolve."""

    note: str = Field(min_length=3, max_length=2000)
    outcome: str = Field(default="resolved", max_length=40)
