"""Storage integrations for e-SewaSathi."""

from app.integrations.storage.base import StorageAdapter, StorageError
from app.integrations.storage.local_storage import LocalStorage

__all__ = ["LocalStorage", "StorageAdapter", "StorageError"]
