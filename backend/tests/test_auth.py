"""Authentication tests: registration, login, invalid login, protected /me."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from conftest import register_and_login


async def test_registration_returns_public_user(client: AsyncClient) -> None:
    response = await client.post(
        "/api/auth/register",
        json={
            "name": "Sita Sharma",
            "email": "sita@example.com",
            "phone": "9801112222",
            "password": "StrongPass@1",
            "confirm_password": "StrongPass@1",
            "preferred_language": "ne",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "sita@example.com"
    assert body["role"] == "citizen"
    assert body["preferred_language"] == "ne"
    assert "password" not in response.text
    assert "password_hash" not in response.text


async def test_registration_rejects_duplicate_email(client: AsyncClient) -> None:
    payload = {
        "name": "Duplicate User",
        "email": "dup@example.com",
        "phone": "9801112223",
        "password": "StrongPass@1",
        "confirm_password": "StrongPass@1",
        "preferred_language": "en",
    }
    first = await client.post("/api/auth/register", json=payload)
    assert first.status_code == 201
    second = await client.post("/api/auth/register", json=payload)
    assert second.status_code == 409
    assert second.json()["detail"] == "An account with this email already exists."


async def test_registration_rejects_mismatched_passwords(client: AsyncClient) -> None:
    response = await client.post(
        "/api/auth/register",
        json={
            "name": "Mismatch User",
            "email": "mismatch@example.com",
            "phone": "9801112224",
            "password": "StrongPass@1",
            "confirm_password": "DifferentPass@1",
            "preferred_language": "en",
        },
    )
    assert response.status_code == 422
    assert "StrongPass@1" not in response.text


async def test_login_success_returns_token(client: AsyncClient) -> None:
    await register_and_login(client, "login-ok@example.com", "LoginPass@1")
    response = await client.post(
        "/api/auth/login",
        json={"email": "login-ok@example.com", "password": "LoginPass@1"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 30
    assert body["user"]["email"] == "login-ok@example.com"
    assert "password" not in response.text


async def test_login_with_wrong_password_is_rejected(client: AsyncClient) -> None:
    await register_and_login(client, "wrongpw@example.com", "LoginPass@1")
    response = await client.post(
        "/api/auth/login",
        json={"email": "wrongpw@example.com", "password": "NotThePassword1"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


async def test_login_with_unknown_email_is_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "WhateverPass@1"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


async def test_me_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.headers.get("www-authenticate") == "Bearer"


async def test_me_returns_current_user(client: AsyncClient) -> None:
    auth = await register_and_login(client, "me@example.com", "LoginPass@1")
    response = await client.get("/api/auth/me", headers=auth["headers"])
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


async def test_me_rejects_garbage_token(client: AsyncClient) -> None:
    response = await client.get(
        "/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401


async def test_logout_is_recorded_in_audit(client: AsyncClient, db: object) -> None:
    auth = await register_and_login(client, "logout@example.com", "LoginPass@1")
    response = await client.post("/api/auth/logout", headers=auth["headers"])
    assert response.status_code == 200

    logs = await db["audit_logs"].find({"action": "user.logout"}).to_list(10)
    assert len(logs) == 1
    assert logs[0]["result"] == "success"
    assert "logout@example.com" not in str(logs[0]["metadata"].get("email"))
