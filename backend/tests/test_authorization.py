"""Authorization tests: protected routes and cross-user access denial."""

from __future__ import annotations

import io

from httpx import AsyncClient

from conftest import create_application, png_bytes, register_and_login


async def test_application_routes_require_token(client: AsyncClient) -> None:
    assert (await client.get("/api/applications")).status_code == 401
    assert (await client.post("/api/applications", json={})).status_code == 401
    assert (await client.get("/api/applications/some-id")).status_code == 401
    assert (await client.delete("/api/applications/some-id")).status_code == 401


async def test_document_routes_require_token(client: AsyncClient) -> None:
    assert (await client.get("/api/applications/some-id/documents")).status_code == 401
    assert (await client.get("/api/documents/some-id/download")).status_code == 401
    assert (await client.delete("/api/documents/some-id")).status_code == 401


async def test_user_routes_require_token(client: AsyncClient) -> None:
    assert (await client.get("/api/users/me")).status_code == 401
    assert (await client.patch("/api/users/me", json={})).status_code == 401


async def test_cross_user_application_read_is_denied(
    client: AsyncClient, citizen: dict[str, str], other_citizen: dict[str, str]
) -> None:
    application = await create_application(client, citizen)

    response = await client.get(
        f"/api/applications/{application['id']}", headers=other_citizen["headers"]
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found."


async def test_cross_user_application_update_is_denied(
    client: AsyncClient, citizen: dict[str, str], other_citizen: dict[str, str]
) -> None:
    application = await create_application(client, citizen)

    response = await client.patch(
        f"/api/applications/{application['id']}",
        headers=other_citizen["headers"],
        json={"form_data": {"full_name": "Hacker"}},
    )
    assert response.status_code == 404


async def test_cross_user_application_cancel_is_denied(
    client: AsyncClient, citizen: dict[str, str], other_citizen: dict[str, str]
) -> None:
    application = await create_application(client, citizen)

    response = await client.delete(
        f"/api/applications/{application['id']}", headers=other_citizen["headers"]
    )
    assert response.status_code == 404


async def test_cross_user_document_access_is_denied(
    client: AsyncClient, citizen: dict[str, str], other_citizen: dict[str, str]
) -> None:
    application = await create_application(client, citizen)
    upload = await client.post(
        f"/api/applications/{application['id']}/documents",
        headers=citizen["headers"],
        data={"document_type": "identity_proof"},
        files={"file": ("id.png", io.BytesIO(png_bytes()), "image/png")},
    )
    assert upload.status_code == 201
    document_id = upload.json()["id"]

    download = await client.get(
        f"/api/documents/{document_id}/download", headers=other_citizen["headers"]
    )
    assert download.status_code == 404

    delete = await client.delete(
        f"/api/documents/{document_id}", headers=other_citizen["headers"]
    )
    assert delete.status_code == 404

    listing = await client.get(
        f"/api/applications/{application['id']}/documents",
        headers=other_citizen["headers"],
    )
    assert listing.status_code == 404


async def test_owner_can_read_own_application(
    client: AsyncClient, citizen: dict[str, str]
) -> None:
    application = await create_application(client, citizen)
    response = await client.get(
        f"/api/applications/{application['id']}", headers=citizen["headers"]
    )
    assert response.status_code == 200
    assert response.json()["id"] == application["id"]


async def test_invalid_application_id_returns_404(
    client: AsyncClient, citizen: dict[str, str]
) -> None:
    response = await client.get(
        "/api/applications/not-a-valid-object-id", headers=citizen["headers"]
    )
    assert response.status_code == 404


async def test_registration_creates_only_citizens(client: AsyncClient) -> None:
    auth = await register_and_login(client, "rolecheck@example.com", "RolePass@1")
    response = await client.get("/api/auth/me", headers=auth["headers"])
    assert response.json()["role"] == "citizen"
