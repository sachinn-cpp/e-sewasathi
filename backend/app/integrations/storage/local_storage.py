"""Private local filesystem storage adapter."""

from __future__ import annotations

import asyncio
from pathlib import Path, PurePosixPath

from app.integrations.storage.base import StorageAdapter, StorageError


class LocalStorage(StorageAdapter):
    """Stores files under a private directory that is never publicly served."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        """Resolve a storage key while blocking path traversal."""
        if not key or key.startswith("/") or "\\" in key:
            raise StorageError("Invalid storage key.")
        parts = PurePosixPath(key).parts
        if any(part in {"..", "."} or part.startswith("/") for part in parts):
            raise StorageError("Invalid storage key.")
        candidate = (self.root / Path(*parts)).resolve()
        if self.root != candidate and self.root not in candidate.parents:
            raise StorageError("Invalid storage key.")
        return candidate

    async def save(self, key: str, data: bytes) -> str:
        path = self._resolve(key)

        def _write() -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = path.with_suffix(path.suffix + ".tmp")
            tmp_path.write_bytes(data)
            tmp_path.replace(path)

        try:
            await asyncio.to_thread(_write)
        except OSError as exc:
            raise StorageError("Could not store the file.") from exc
        return key

    async def read(self, key: str) -> bytes:
        path = self._resolve(key)

        def _read() -> bytes:
            return path.read_bytes()

        try:
            return await asyncio.to_thread(_read)
        except FileNotFoundError as exc:
            raise StorageError("Stored file not found.") from exc
        except OSError as exc:
            raise StorageError("Could not read the file.") from exc

    async def delete(self, key: str) -> bool:
        path = self._resolve(key)

        def _delete() -> bool:
            if path.exists():
                path.unlink()
                return True
            return False

        try:
            return await asyncio.to_thread(_delete)
        except OSError as exc:
            raise StorageError("Could not delete the file.") from exc

    async def exists(self, key: str) -> bool:
        path = self._resolve(key)
        return await asyncio.to_thread(path.exists)
