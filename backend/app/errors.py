"""Shared application errors with safe, user facing messages."""

from __future__ import annotations


class AppError(Exception):
    """Business rule violation returned as a safe JSON error response."""

    def __init__(self, detail: str, status_code: int = 400) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class NotFoundError(AppError):
    def __init__(self, detail: str = "Resource not found.") -> None:
        super().__init__(detail, status_code=404)


class ConflictError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, status_code=409)


class UnauthorizedError(AppError):
    def __init__(self, detail: str = "Not authenticated.") -> None:
        super().__init__(detail, status_code=401)


class ForbiddenError(AppError):
    def __init__(self, detail: str = "You do not have permission to perform this action.") -> None:
        super().__init__(detail, status_code=403)


class ConsentRequiredError(AppError):
    """Raised when a sensitive action is attempted without valid consent."""

    def __init__(self, details: dict | None = None) -> None:
        from app.utils.error_codes import CONSENT_REQUIRED, message_for

        super().__init__(message_for(CONSENT_REQUIRED), status_code=403)
        self.code = CONSENT_REQUIRED
        self.details = details or {}
