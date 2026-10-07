"""Shared pytest fixtures for the e-SewaSathi backend test suite.

Environment is configured before any application import so that tests always
run against an isolated database and an isolated upload directory.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pymongo import AsyncMongoClient

_TEST_DB_NAME = "e_sewasathi_test"
os.environ["MONGO_DB_NAME"] = _TEST_DB_NAME
os.environ["DEMO_MODE"] = "true"
os.environ["JWT_SECRET"] = "test-secret-not-for-production-use"
os.environ["UPLOAD_DIR"] = os.path.join(
    tempfile.gettempdir(), "e_sewasathi_test_uploads"
)
os.environ["BCRYPT_ROUNDS"] = "4"

from app.config import get_settings  # noqa: E402
from app.database.indexes import ensure_indexes  # noqa: E402
from app.dependencies import get_db, get_storage_dep  # noqa: E402
from app.integrations.storage.local_storage import LocalStorage  # noqa: E402
from app.main import app  # noqa: E402

TEST_MONGO_URI = get_settings().mongo_uri


@pytest_asyncio.fixture
async def db() -> AsyncIterator[object]:
    """A fresh, empty test database with Phase 1 indexes."""
    client = AsyncMongoClient(TEST_MONGO_URI, serverSelectionTimeoutMS=5000)
    await client.admin.command("ping")
    database = client[_TEST_DB_NAME]
    await client.drop_database(_TEST_DB_NAME)
    await ensure_indexes(database)
    yield database
    await client.drop_database(_TEST_DB_NAME)
    await client.close()


@pytest_asyncio.fixture
async def storage(tmp_path: Path) -> LocalStorage:
    """A private storage root unique to each test."""
    return LocalStorage(tmp_path / "uploads")


@pytest_asyncio.fixture
async def client(db: object, storage: LocalStorage) -> AsyncIterator[AsyncClient]:
    """HTTP client wired to the ASGI app with test database and storage."""
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_storage_dep] = lambda: storage
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def citizen(client: AsyncClient) -> dict[str, str]:
    """A registered and signed-in citizen (user A)."""
    return await register_and_login(client, "citizen-a@example.com", "CitizenA@123")


@pytest_asyncio.fixture
async def other_citizen(client: AsyncClient) -> dict[str, str]:
    """A second registered and signed-in citizen (user B)."""
    return await register_and_login(client, "citizen-b@example.com", "CitizenB@123")


async def register_and_login(
    client: AsyncClient,
    email: str,
    password: str,
    name: str = "Test Citizen",
    phone: str = "9800000000",
) -> dict[str, str]:
    """Register an account and return its auth context."""
    response = await client.post(
        "/api/auth/register",
        json={
            "name": name,
            "email": email,
            "phone": phone,
            "password": password,
            "confirm_password": password,
            "preferred_language": "en",
        },
    )
    assert response.status_code == 201, response.text
    user = response.json()

    login = await client.post(
        "/api/auth/login", json={"email": email, "password": password}
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return {
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
        "email": email,
        "password": password,
        "user_id": user["id"],
    }


async def create_application(client: AsyncClient, auth: dict[str, str]) -> dict:
    """Create an income certificate application for the given user."""
    response = await client.post(
        "/api/applications",
        headers=auth["headers"],
        json={"service_type": "income_certificate", "preferred_language": "en"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def png_bytes(size: int = 64) -> bytes:
    """Minimal bytes that pass PNG magic byte validation."""
    return b"\x89PNG\r\n\x1a\n" + b"\x00" * max(size - 8, 0)


def jpeg_bytes(size: int = 64) -> bytes:
    return b"\xff\xd8\xff\xe0" + b"\x00" * max(size - 4, 0)


def pdf_bytes(size: int = 64) -> bytes:
    return b"%PDF-1.4\n" + b"\x00" * max(size - 9, 0)
