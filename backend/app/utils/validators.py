"""Field level validators used by schemas and services."""

from __future__ import annotations

import re
import secrets
from datetime import datetime, timezone

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_PATTERN = re.compile(r"^\+?[0-9\-\s]{7,15}$")
SAFE_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")
IDEMPOTENCY_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,64}$")

SUPPORTED_LANGUAGE_CODES: tuple[str, ...] = ("en", "hi", "ne")


def normalize_email(email: str) -> str:
    """Lowercase and trim an email address."""
    return email.strip().lower()


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.match(normalize_email(email)))


def is_valid_phone(phone: str) -> bool:
    return bool(PHONE_PATTERN.match(phone.strip()))


def safe_filename(raw_name: str, fallback: str = "document") -> str:
    """Sanitize a user supplied filename for display in downloads."""
    base = raw_name.replace("\\", "/").split("/")[-1].strip()
    base = SAFE_FILENAME_PATTERN.sub("_", base).strip("._")
    if not base:
        return fallback
    return base[:120]


def generate_application_number() -> str:
    """Generate a human friendly application number such as ESW-2026-4F2A9C."""
    year = datetime.now(timezone.utc).year
    suffix = secrets.token_hex(3).upper()
    return f"ESW-{year}-{suffix}"


def normalize_language_code(code: str | None) -> str:
    """Normalize a language tag to a supported code, defaulting to English."""
    if not code:
        return "en"
    base = code.strip().lower().replace("_", "-").split("-")[0]
    return base if base in SUPPORTED_LANGUAGE_CODES else "en"


def is_valid_language_code(code: str | None) -> bool:
    return bool(code) and normalize_language_code(code) == code.strip().lower()


def is_valid_idempotency_key(key: str) -> bool:
    return bool(IDEMPOTENCY_KEY_PATTERN.match(key or ""))
