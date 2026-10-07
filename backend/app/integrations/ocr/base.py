"""OCR adapter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class OCRResult:
    """Structured output of one document extraction."""

    extracted: dict[str, str] = field(default_factory=dict)
    confidence: float = 0.0
    ambiguous_fields: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    provider: str = "demo"


class OCRClient(ABC):
    """Document extraction adapter (demo, PaddleOCR, ...)."""

    @abstractmethod
    async def extract(
        self,
        data: bytes,
        mime_type: str,
        filename: str,
        language: str = "en",
        context: dict[str, Any] | None = None,
    ) -> OCRResult:
        """Extract form fields from a document image or PDF."""
