"""JWT creation and validation helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.config import get_settings


class TokenError(Exception):
    """Raised when a JWT is missing, expired or malformed."""


def create_access_token(user_id: str, role: str) -> str:
    """Create a signed JWT for the given user id and role."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
        "iss": "e-SewaSathi",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT, raising TokenError on any problem."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            issuer="e-SewaSathi",
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("Session expired. Please sign in again.") from exc
    except jwt.PyJWTError as exc:
        raise TokenError("Invalid authentication token.") from exc
    if not payload.get("sub"):
        raise TokenError("Invalid authentication token.")
    return payload


