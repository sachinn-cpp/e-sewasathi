"""Structured error codes and safe user-facing messages."""

from __future__ import annotations

from typing import Any

CONSENT_REQUIRED = "CONSENT_REQUIRED"
PORTAL_TIMEOUT = "PORTAL_TIMEOUT"
PORTAL_UNAVAILABLE = "PORTAL_UNAVAILABLE"
PORTAL_INVALID_FIELD = "PORTAL_INVALID_FIELD"
PORTAL_UNKNOWN_RESULT = "PORTAL_UNKNOWN_RESULT"
PORTAL_DOCUMENT_MISMATCH = "PORTAL_DOCUMENT_MISMATCH"
SUBMISSION_BLOCKED = "SUBMISSION_BLOCKED"
WORKFLOW_NOT_FOUND = "WORKFLOW_NOT_FOUND"
INTERRUPT_MISMATCH = "INTERRUPT_MISMATCH"
ESCALATION_OPEN = "ESCALATION_OPEN"
DATA_VERSION_MISMATCH = "DATA_VERSION_MISMATCH"
DEMO_MODE_ONLY = "DEMO_MODE_ONLY"
NOT_CONFIGURED = "NOT_CONFIGURED"

_MESSAGES: dict[str, str] = {
    CONSENT_REQUIRED: "Explicit user consent is required.",
    PORTAL_TIMEOUT: "The government portal did not respond in time.",
    PORTAL_UNAVAILABLE: "The government portal is temporarily unavailable.",
    PORTAL_INVALID_FIELD: "The portal rejected a form field.",
    PORTAL_UNKNOWN_RESULT: "The portal submission result is unknown.",
    PORTAL_DOCUMENT_MISMATCH: "The portal reported a document mismatch.",
    SUBMISSION_BLOCKED: "This application is not ready for submission.",
    WORKFLOW_NOT_FOUND: "No workflow was found for this application.",
    INTERRUPT_MISMATCH: "The provided resume does not match the pending action.",
    ESCALATION_OPEN: "An escalation is already open for this application.",
    DATA_VERSION_MISMATCH: "The application data changed. Please review again.",
    DEMO_MODE_ONLY: "This feature runs in demo mode only.",
    NOT_CONFIGURED: "This provider is not configured in the current environment.",
}


def message_for(code: str) -> str:
    return _MESSAGES.get(code, "The request could not be completed.")


def error_payload(
    code: str, message: str = "", details: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Build the standard error body: {"success": false, "error": {...}}."""
    body: dict[str, Any] = {
        "success": False,
        "error": {"code": code, "message": message or message_for(code)},
    }
    if details:
        body["error"]["details"] = details
    return body
