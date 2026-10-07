"""Workflow and agent schemas for Phase 2."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    WAITING_USER = "waiting_user"
    WAITING_CONSENT = "waiting_consent"
    WAITING_HELPER = "waiting_helper"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"
    PAUSED = "paused"


class PendingInterruptOut(BaseModel):
    """The interruption the workflow is waiting on."""

    name: str
    payload: dict[str, Any] = Field(default_factory=dict)


class WorkflowStepOut(BaseModel):
    node: str
    entered_at: datetime


class WorkflowOut(BaseModel):
    """Public view of an application workflow run."""

    application_id: str
    user_id: str
    status: WorkflowStatus
    current_node: str = ""
    pending_interrupt: PendingInterruptOut | None = None
    retry_count: int = 0
    data_version: int = 1
    steps: list[WorkflowStepOut] = Field(default_factory=list)
    last_error: str = ""
    created_at: datetime
    updated_at: datetime


class WorkflowResumeRequest(BaseModel):
    """Payload for POST /api/agent/applications/{application_id}/resume."""

    interrupt_name: str = Field(min_length=1, max_length=80)
    value: dict[str, Any] = Field(default_factory=dict)


class WorkflowRunResponse(BaseModel):
    """Result of running or resuming a workflow."""

    application_id: str
    status: WorkflowStatus
    current_node: str = ""
    pending_interrupt: PendingInterruptOut | None = None
    changed: bool = True
