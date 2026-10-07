"""Application-level field encryption helpers.

Uses Fernet (symmetric AES) from the cryptography package with a key derived
from ``settings.encryption_key`` so no raw secret is stored in code.
"""

from __future__ import annotations

import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings

PREFIX = "enc:v1:"


@lru_cache(maxsize=4)
def _fernet(key_material: str) -> Fernet:
    digest = hashlib.sha256(key_material.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_field(value: str) -> str:
    """Encrypt a sensitive string for at-rest storage."""
    if not value:
        return value
    token = _fernet(get_settings().encryption_key).encrypt(value.encode("utf-8"))
    return PREFIX + token.decode("ascii")


def decrypt_field(value: str) -> str:
    """Decrypt a value produced by :func:`encrypt_field`."""
    if not value:
        return value
    if not value.startswith(PREFIX):
        return value
    try:
        token = value[len(PREFIX) :].encode("ascii")
        return _fernet(get_settings().encryption_key).decrypt(token).decode("utf-8")
    except (InvalidToken, ValueError):
        return ""


def is_encrypted(value: str) -> bool:
    return value.startswith(PREFIX)
