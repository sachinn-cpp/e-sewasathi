"""Storage adapter interface. Phase 1 ships local storage; cloud storage
adapters will implement the same interface in a later phase."""

from __future__ import annotations

from abc import ABC, abstractmethod


class StorageError(Exception):
    """Raised when a storage operation fails safely."""


class StorageAdapter(ABC):
    """Abstract private object storage."""

    @abstractmethod
    async def save(self, key: str, data: bytes) -> str:
        """Persist bytes under a server generated key and return the key."""

    @abstractmethod
    async def read(self, key: str) -> bytes:
        """Read bytes for a key. Raises StorageError when missing."""

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete an object. Returns False when it did not exist."""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Return True when the object exists."""
