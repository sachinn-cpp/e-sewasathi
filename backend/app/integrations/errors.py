"""Shared integration errors (no web framework dependencies)."""


class IntegrationError(Exception):
    """Base error for external adapters."""

    code = "INTEGRATION_ERROR"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ProviderNotConfiguredError(IntegrationError):
    code = "NOT_CONFIGURED"


class ProviderUnavailableError(IntegrationError):
    code = "PROVIDER_UNAVAILABLE"
