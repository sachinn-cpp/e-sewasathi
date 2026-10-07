"""Deterministic demo OCR client (no model downloads, reproducible output)."""

from __future__ import annotations

import hashlib
from typing import Any

from app.integrations.ocr.base import OCRClient, OCRResult

_BY_DOCUMENT_TYPE: dict[str, list[str]] = {
    "identity_proof": ["full_name", "date_of_birth", "citizenship_number"],
    "address_proof": ["address", "district", "municipality", "ward_no"],
    "income_proof": ["annual_income", "employment_status"],
    "photograph": [],
}


class DemoOCRClient(OCRClient):
    """Fake extraction with deterministic values and test hooks.

    Filename hooks (checked case-insensitively):
    - contains "blur" or "low"  -> low confidence and ambiguous fields
    - contains "conflict"      -> value that differs from the form (conflict)
    """

    provider = "demo"

    async def extract(
        self,
        data: bytes,
        mime_type: str,
        filename: str,
        language: str = "en",
        context: dict[str, Any] | None = None,
    ) -> OCRResult:
        context = context or {}
        lowered = (filename or "").lower()
        document_type = str(context.get("document_type", "identity_proof"))
        form_data = dict(context.get("form_data") or {})
        user_name = str(context.get("user_name", "")) or form_data.get("full_name", "")

        digest = hashlib.sha256((filename or "doc").encode("utf-8")).hexdigest()
        ward = str(1 + int(digest[:4], 16) % 32)

        extracted: dict[str, str] = {}
        for field_name in _BY_DOCUMENT_TYPE.get(document_type, []):
            extracted[field_name] = self._value_for(
                field_name, form_data, user_name, digest, ward
            )

        if "conflict" in lowered and extracted:
            first = next(iter(extracted))
            extracted[first] = (extracted[first] or "Demo Person") + " (Portal Copy)"

        if "blur" in lowered or "low" in lowered:
            return OCRResult(
                extracted=extracted,
                confidence=0.34,
                ambiguous_fields=["full_name", "date_of_birth"],
                issues=["The image looks blurry. Please confirm the highlighted values."],
                provider=self.provider,
            )

        return OCRResult(
            extracted=extracted,
            confidence=0.93,
            ambiguous_fields=[],
            issues=[],
            provider=self.provider,
        )

    @staticmethod
    def _value_for(
        field_name: str,
        form_data: dict[str, Any],
        user_name: str,
        digest: str,
        ward: str,
    ) -> str:
        if field_name == "full_name":
            return str(form_data.get("full_name") or user_name or "Demo Citizen")
        if field_name == "date_of_birth":
            return str(form_data.get("date_of_birth") or "1992-05-14")
        if field_name == "citizenship_number":
            return f"{int(digest[:6], 16) % 900000 + 100000}-0-{digest[6:9].upper()}"
        if field_name == "address":
            return str(form_data.get("address") or "12 Demo Street, Ward " + ward)
        if field_name == "district":
            return str(form_data.get("district") or "Kathmandu")
        if field_name == "municipality":
            return str(form_data.get("municipality") or "Kathmandu Metropolitan City")
        if field_name == "ward_no":
            return str(form_data.get("ward_no") or ward)
        if field_name == "annual_income":
            return str(form_data.get("annual_income") or "360000")
        if field_name == "employment_status":
            return str(form_data.get("employment_status") or "Salaried")
        return ""
