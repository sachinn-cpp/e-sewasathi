"""PII masking helpers used before writing audit metadata."""

from __future__ import annotations

from typing import Any


def mask_email(email: str) -> str:
    """citizen@example.com -> c***n@example.com"""
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[:1] + "*"
    else:
        masked_local = local[0] + "***" + local[-1]
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """0987654321 -> ******4321"""
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) <= 4:
        return "*" * len(digits)
    return "*" * (len(digits) - 4) + digits[-4:]


def mask_name(name: str) -> str:
    """Sita Sharma -> S***a S***a"""
    parts = []
    for part in name.split():
        if len(part) <= 1:
            parts.append("*")
        else:
            parts.append(part[0] + "***" + part[-1])
    return " ".join(parts) if parts else "***"


def mask_value(key: str, value: Any) -> Any:
    """Mask a single value based on the field name."""
    key_l = key.lower()
    if not isinstance(value, str):
        return value
    if "email" in key_l:
        return mask_email(value)
    if "phone" in key_l or "mobile" in key_l:
        return mask_phone(value)
    if key_l in {"name", "full_name", "citizen_name"}:
        return mask_name(value)
    if key_l in {"password", "password_hash", "token", "access_token"}:
        return "[REDACTED]"
    if key_l in {"citizenship_number", "citizenship", "pan_number", "bank_account"}:
        return value[:2] + "***" + value[-2:] if len(value) > 4 else "***"
    return value


def mask_metadata(data: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of metadata with sensitive fields masked."""
    return {key: mask_value(key, value) for key, value in data.items()}
