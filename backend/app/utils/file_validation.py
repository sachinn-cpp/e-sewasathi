"""Upload validation: MIME type, magic bytes, size and SHA-256 hashing."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from app.config import get_settings

MAGIC_SIGNATURES: dict[str, tuple[bytes, ...]] = {
    "application/pdf": (b"%PDF-",),
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
}

EXTENSION_BY_MIME: dict[str, str] = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}


class FileValidationError(Exception):
    """Raised when an uploaded file fails validation."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass(slots=True)
class ValidatedFile:
    data: bytes
    mime_type: str
    extension: str
    size: int
    sha256: str


def detect_mime(data: bytes) -> str | None:
    """Detect the real content type from file magic bytes."""
    for mime, signatures in MAGIC_SIGNATURES.items():
        if any(data.startswith(signature) for signature in signatures):
            return mime
    return None


def validate_upload(
    data: bytes,
    declared_content_type: str | None,
    max_bytes: int | None = None,
) -> ValidatedFile:
    """Validate size and content of an uploaded file.

    Both the declared Content-Type and the magic bytes must agree on an
    allowed type. Anything else is rejected.
    """
    settings = get_settings()
    limit = max_bytes if max_bytes is not None else settings.max_file_size_bytes

    if not data:
        raise FileValidationError("The uploaded file is empty.")

    if len(data) > limit:
        raise FileValidationError(
            f"File is too large. Maximum allowed size is {settings.max_file_size_mb} MB.",
            status_code=413,
        )

    sniffed = detect_mime(data)
    if sniffed is None:
        raise FileValidationError("Unsupported file type. Allowed types: PDF, JPEG, PNG.")

    declared = (declared_content_type or "").split(";")[0].strip().lower()
    if declared and declared not in settings.allowed_mime_types:
        raise FileValidationError("Unsupported file type. Allowed types: PDF, JPEG, PNG.")
    if declared and declared != sniffed:
        raise FileValidationError("File content does not match its declared type.")

    return ValidatedFile(
        data=data,
        mime_type=sniffed,
        extension=EXTENSION_BY_MIME[sniffed],
        size=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
    )
