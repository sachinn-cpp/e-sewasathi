"""Mock government portal client interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

ACCEPTED = "accepted"
DUPLICATE = "duplicate"
INVALID_FIELD = "invalid_field"
DOCUMENT_MISMATCH = "document_mismatch"
TIMEOUT = "timeout"
SERVER_ERROR = "server_error"
UNKNOWN_RESULT = "unknown_result"

RECOVERABLE_OUTCOMES: frozenset[str] = frozenset(
    {TIMEOUT, SERVER_ERROR, UNKNOWN_RESULT}
)


@dataclass
class PortalSubmitResult:
    """Outcome of one portal submission attempt."""

    outcome: str
    application_number: str = ""
    reference: str = ""
    field: str = ""
    message: str = ""
    http_status: int = 0
    already_processed: bool = False


@dataclass
class PortalStatusResult:
    """Outcome of a portal status lookup."""

    found: bool
    status: str = ""
    application_number: str = ""
    reference: str = ""
    message: str = ""
    checked_at: str = ""
    lookup_error: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


class PortalClient(ABC):
    """Government portal adapter (mock API now, Playwright later)."""

    @abstractmethod
    async def get_requirements(self, service_type: str) -> dict[str, Any]:
        """Fetch portal requirements for a service."""

    @abstractmethod
    async def submit_application(
        self, payload: dict[str, Any], idempotency_key: str
    ) -> PortalSubmitResult:
        """Submit an application, safe to retry with the same key."""

    @abstractmethod
    async def get_application_status(self, application_number: str) -> PortalStatusResult:
        """Look up a submission by portal application number."""

    @abstractmethod
    async def find_submission(self, idempotency_key: str) -> PortalStatusResult:
        """Look up a submission by idempotency key (before any retry)."""

    async def close(self) -> None:
        """Release network resources."""
