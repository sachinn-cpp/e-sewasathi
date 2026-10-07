"""HTTP client for the mock government portal (PORTAL_MODE=api)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.integrations.errors import ProviderUnavailableError
from app.integrations.portal.base import (
    ACCEPTED,
    DUPLICATE,
    DOCUMENT_MISMATCH,
    INVALID_FIELD,
    SERVER_ERROR,
    TIMEOUT,
    UNKNOWN_RESULT,
    PortalClient,
    PortalStatusResult,
    PortalSubmitResult,
)

logger = logging.getLogger(__name__)


class MockPortalClient(PortalClient):
    """Talks to the FastAPI backend of mock-government-portal."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 10.0,
        api_token: str = "",
        username: str = "officer",
        password: str = "demo-officer",
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password or api_token or "demo-officer"
        self._client = http_client or httpx.AsyncClient(
            base_url=self.base_url, timeout=timeout
        )
        self._owns_client = http_client is None
        self._token = api_token
        self.status_checks: list[str] = []

    async def _login(self) -> str:
        try:
            response = await self._client.post(
                "/portal/auth/login",
                json={"username": self.username, "password": self.password},
            )
            response.raise_for_status()
            body = response.json()
            self._token = str(body.get("access_token", ""))
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(
                "The government portal could not be reached."
            ) from exc
        if not self._token:
            raise ProviderUnavailableError("The portal did not return a session token.")
        return self._token

    async def _auth_headers(self) -> dict[str, str]:
        if not self._token:
            await self._login()
        return {"Authorization": f"Bearer {self._token}"}

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
    ) -> httpx.Response:
        headers = await self._auth_headers()
        response = await self._client.request(
            method, path, json=json_body, params=params, headers=headers
        )
        if response.status_code == 401:
            headers = await self._login()
            response = await self._client.request(
                method, path, json=json_body, params=params, headers=headers
            )
        return response

    async def get_requirements(self, service_type: str) -> dict[str, Any]:
        try:
            response = await self._request(
                "GET", f"/portal/services/{service_type}/requirements"
            )
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(
                "The government portal could not be reached."
            ) from exc
        if response.status_code != 200:
            raise ProviderUnavailableError("Portal requirements are unavailable.")
        return response.json()

    async def submit_application(
        self, payload: dict[str, Any], idempotency_key: str
    ) -> PortalSubmitResult:
        body = {**payload, "idempotency_key": idempotency_key}
        try:
            response = await self._request("POST", "/portal/applications", json_body=body)
        except httpx.TimeoutException:
            return PortalSubmitResult(outcome=TIMEOUT, message="Portal timed out.")
        except httpx.HTTPError as exc:
            logger.warning("Portal submit failed: %s", type(exc).__name__)
            return PortalSubmitResult(
                outcome=SERVER_ERROR, message="Portal connection failed."
            )
        return self._map_submit_response(response)

    @staticmethod
    def _map_submit_response(response: httpx.Response) -> PortalSubmitResult:
        status = response.status_code
        try:
            data = response.json()
        except ValueError:
            data = {}

        if status in (200, 201):
            return PortalSubmitResult(
                outcome=ACCEPTED,
                application_number=str(data.get("application_number", "")),
                reference=str(
                    data.get("submission_reference") or data.get("reference") or ""
                ),
                http_status=status,
            )
        if status == 409:
            return PortalSubmitResult(
                outcome=DUPLICATE,
                application_number=str(data.get("application_number", "")),
                reference=str(data.get("submission_reference", "")),
                message=str(data.get("message", "Already submitted.")),
                http_status=status,
                already_processed=True,
            )
        if status == 504:
            return PortalSubmitResult(
                outcome=TIMEOUT, message="Portal gateway timed out.", http_status=status
            )

        error = data.get("error") or {}
        code = str(error.get("code", ""))
        message = str(error.get("message", ""))
        if status == 422:
            if code == DOCUMENT_MISMATCH or "mismatch" in message.lower():
                return PortalSubmitResult(
                    outcome=DOCUMENT_MISMATCH,
                    field=str(error.get("field", "")),
                    message=message or "Document mismatch reported by the portal.",
                    http_status=status,
                )
            return PortalSubmitResult(
                outcome=INVALID_FIELD,
                field=str(error.get("field", "")),
                message=message or "Portal rejected a form field.",
                http_status=status,
            )
        if status >= 500:
            outcome = UNKNOWN_RESULT if code == UNKNOWN_RESULT else SERVER_ERROR
            return PortalSubmitResult(
                outcome=outcome,
                message=message or "Portal server error.",
                http_status=status,
            )
        return PortalSubmitResult(
            outcome=SERVER_ERROR,
            message=message or "Unexpected portal response.",
            http_status=status,
        )

    async def get_application_status(
        self, application_number: str
    ) -> PortalStatusResult:
        try:
            response = await self._request(
                "GET", f"/portal/applications/{application_number}"
            )
        except httpx.HTTPError as exc:
            return PortalStatusResult(
                found=False,
                lookup_error=True,
                message=f"Status lookup failed: {type(exc).__name__}",
            )
        return self._map_status_response(response)

    async def find_submission(self, idempotency_key: str) -> PortalStatusResult:
        self.status_checks.append(idempotency_key)
        try:
            response = await self._request(
                "GET", "/portal/applications", params={"idempotency_key": idempotency_key}
            )
        except httpx.HTTPError as exc:
            return PortalStatusResult(
                found=False,
                lookup_error=True,
                message=f"Status lookup failed: {type(exc).__name__}",
            )
        if response.status_code == 404:
            return PortalStatusResult(found=False, message="Not found.")
        return self._map_status_response(response, by_key=True)

    @staticmethod
    def _map_status_response(
        response: httpx.Response, by_key: bool = False
    ) -> PortalStatusResult:
        if response.status_code == 404:
            return PortalStatusResult(found=False, message="Not found.")
        if response.status_code >= 500:
            return PortalStatusResult(
                found=False,
                lookup_error=True,
                message="Portal status lookup failed.",
            )
        if response.status_code != 200:
            return PortalStatusResult(
                found=False, lookup_error=True, message="Unexpected response."
            )
        data = response.json()
        if by_key and not data.get("found", True):
            return PortalStatusResult(found=False, message="Not found.")
        return PortalStatusResult(
            found=True,
            status=str(data.get("status", "")),
            application_number=str(data.get("application_number", "")),
            reference=str(data.get("submission_reference", "")),
            message=str(data.get("message", "")),
            checked_at=str(data.get("updated_at", "")),
            extra={k: v for k, v in data.items() if k.startswith("simulation_")},
        )

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()
