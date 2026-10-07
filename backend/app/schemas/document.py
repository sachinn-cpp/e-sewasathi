"""Document schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class DocumentType(str, Enum):
    """Documents required for the income certificate service."""

    IDENTITY_PROOF = "identity_proof"
    ADDRESS_PROOF = "address_proof"
    INCOME_PROOF = "income_proof"
    PHOTOGRAPH = "photograph"


REQUIRED_DOCUMENT_TYPES: tuple[str, ...] = (
    DocumentType.IDENTITY_PROOF.value,
    DocumentType.ADDRESS_PROOF.value,
    DocumentType.INCOME_PROOF.value,
    DocumentType.PHOTOGRAPH.value,
)


class ValidationStatus(str, Enum):
    """Result of basic server side document validation."""

    VALIDATED = "validated"
    REJECTED = "rejected"
    PENDING = "pending"


class DocumentOut(BaseModel):
    """Public representation of an uploaded document."""

    id: str
    application_id: str
    document_type: DocumentType
    safe_filename: str
    file_size: int
    mime_type: str
    validation_status: ValidationStatus
    created_at: datetime
