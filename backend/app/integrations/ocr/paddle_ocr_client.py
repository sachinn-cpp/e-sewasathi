"""PaddleOCR adapter (optional; requires the local paddleocr pipeline)."""

from __future__ import annotations

from typing import Any

from app.integrations.errors import ProviderNotConfiguredError
from app.integrations.ocr.base import OCRClient, OCRResult


class PaddleOCRClient(OCRClient):
    """Real OCR via PaddleOCR.

    The local inference pipeline (image decoding, angle classification) is not
    wired in this environment, so the adapter reports NOT_CONFIGURED instead of
    pretending to extract data. Wire a worker service here when paddleocr is
    deployed.
    """

    provider = "paddle"

    async def extract(
        self,
        data: bytes,
        mime_type: str,
        filename: str,
        language: str = "en",
        context: dict[str, Any] | None = None,
    ) -> OCRResult:
        raise ProviderNotConfiguredError(
            "OCR provider 'paddle' is not configured. Install paddleocr and wire "
            "the inference pipeline, or use the demo OCR provider."
        )
