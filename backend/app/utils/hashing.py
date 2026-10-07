"""Password hashing helpers (bcrypt)."""

from __future__ import annotations

import bcrypt

from app.config import get_settings


def hash_password(password: str) -> str:
    """Hash a password with a per-password salt."""
    rounds = get_settings().bcrypt_rounds
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Constant-shape password verification. Returns False on any failure."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False
