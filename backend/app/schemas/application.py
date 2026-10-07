"""Application schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ServiceType(str, Enum):
    """Government services supported in Phase 1."""

    INCOME_CERTIFICATE = "income_certificate"


class ApplicationStatus(str, Enum):
    """Lifecycle states: Phase 1 plus the Phase 2 agent workflow."""

    DRAFT = "draft"
    DOCUMENTS_PENDING = "documents_pending"
    AWAITING_USER_REVIEW = "awaiting_user_review"
    CANCELLED = "cancelled"
    DOCUMENTS_UNDER_REVIEW = "documents_under_review"
    AWAITING_CONSENT = "awaiting_consent"
    SUBMITTING = "submitting"
    SUBMITTED = "submitted"
    UNDER_GOVERNMENT_REVIEW = "under_government_review"
    ACTION_REQUIRED = "action_required"
    ESCALATED = "escalated"
    COMPLETED = "completed"
    FAILED = "failed"


ACTIVE_STATUSES: tuple[ApplicationStatus, ...] = (
    ApplicationStatus.DRAFT,
    ApplicationStatus.DOCUMENTS_PENDING,
    ApplicationStatus.AWAITING_USER_REVIEW,
)


class IncomeCertificateFormData(BaseModel):
    """Basic form data for an income certificate application."""

    full_name: str = Field(default="", max_length=120)
    date_of_birth: str = Field(default="", max_length=40)
    citizenship_number: str = Field(default="", max_length=40)
    address: str = Field(default="", max_length=300)
    district: str = Field(default="", max_length=100)
    municipality: str = Field(default="", max_length=100)
    ward_no: str = Field(default="", max_length=10)
    employment_status: str = Field(default="", max_length=60)
    annual_income: str = Field(default="", max_length=40)
    purpose: str = Field(default="", max_length=300)
    preferred_language: str = Field(default="en", max_length=10)

    def is_complete(self) -> bool:
        """True when the minimum required fields are filled."""
        required = (self.full_name, self.address, self.district, self.annual_income, self.purpose)
        return all(value.strip() for value in required)


class ApplicationCreate(BaseModel):
    """Payload for POST /api/applications."""

    service_type: ServiceType = ServiceType.INCOME_CERTIFICATE
    form_data: IncomeCertificateFormData = Field(default_factory=IncomeCertificateFormData)
    preferred_language: str = Field(default="en", max_length=10)


class ApplicationUpdate(BaseModel):
    """Payload for PATCH /api/applications/{application_id}."""

    form_data: IncomeCertificateFormData | None = None
    status: ApplicationStatus | None = None


class ApplicationOut(BaseModel):
    """Public representation of an application."""

    id: str
    user_id: str
    service_type: ServiceType
    status: ApplicationStatus
    current_step: str
    progress_percent: int
    form_data: IncomeCertificateFormData
    data_version: int
    application_number: str
    document_count: int = 0
    created_at: datetime
    updated_at: datetime
