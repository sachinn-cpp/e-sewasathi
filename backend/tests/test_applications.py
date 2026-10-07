"""Application lifecycle tests: creation, listing, updates, cancellation, audit."""

from __future__ import annotations

from httpx import AsyncClient

from conftest import create_application


async def test_create_income_certificate_application(
    client: AsyncClient, citizen: dict[str, str]
) -> None:
    response = await client.post(
        "/api/applications",
        headers=citizen["headers"],
        json={"service_type": "income_certificate", "preferred_language": "ne"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["service_type"] == "income_certificate"
    assert body["status"] == "draft"
    assert body["data_version"] == 1
    assert body["progress_percent"] == 0
    assert body["current_step"] == "form"
    assert body["application_number"].startswith("ESW-")
    assert body["user_id"] == citizen["user_id"]
    assert body["document_count"] == 0


async def test_list_contains_only_my_applications(
    client: AsyncClient, citizen: dict[str, str], other_citizen: dict[str, str]
) -> None:
    first = await create_application(client, citizen)
    await create_application(client, citizen)
    await create_application(client, other_citizen)

    response = await client.get("/api/applications", headers=citizen["headers"])
    assert response.status_code == 200
    applications = response.json()
    assert len(applications) == 2
    ids = {item["id"] for item in applications}
    assert first["id"] in ids
    assert all(item["user_id"] == citizen["user_id"] for item in applications)


async def test_get_application_returns_full_payload(
    client: AsyncClient, citizen: dict[str, str]
) -> None:
    application = await create_application(client, citizen)
    response = await client.get(
        f"/api/applications/{application['id']}", headers=citizen["headers"]
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == application["id"]
    assert "form_data" in body
    assert "created_at" in body


async def test_update_form_data_increments_data_version(
    client: AsyncClient, citizen: dict[str, str]
) -> None:
    application = await create_application(client, citizen)
    payload = {
        "form_data": {
            "full_name": "Ram Bahadur",
            "address": "Ward 5, Kathmandu",
            "district": "Kathmandu",
            "annual_income": "240000",
            "purpose": "Scholarship application",
        }
    }
    response = await client.patch(
        f"/api/applications/{application['id']}",
        headers=citizen["headers"],
        json=payload,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data_version"] == application["data_version"] + 1
    assert body["form_data"]["full_name"] == "Ram Bahadur"
    assert body["current_step"] == "documents"
    assert body["progress_percent"] == 40

    second = await client.patch(
        f"/api/applications/{application['id']}",
        headers=citizen["headers"],
        json=payload,
    )
    assert second.status_code == 200
    assert second.json()["data_version"] == body["data_version"] + 1


async def test_cancel_application_via_delete(
    client: AsyncClient, citizen: dict[str, str]
) -> None:
    application = await create_application(client, citizen)
    response = await client.delete(
        f"/api/applications/{application['id']}", headers=citizen["headers"]
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert response.json()["current_step"] == "cancelled"

    again = await client.delete(
        f"/api/applications/{application['id']}", headers=citizen["headers"]
    )
    assert again.status_code == 200
    assert again.json()["status"] == "cancelled"


async def test_cancelled_application_cannot_be_edited(
    client: AsyncClient, citizen: dict[str, str]
) -> None:
    application = await create_application(client, citizen)
    await client.delete(
        f"/api/applications/{application['id']}", headers=citizen["headers"]
    )
    response = await client.patch(
        f"/api/applications/{application['id']}",
        headers=citizen["headers"],
        json={"form_data": {"full_name": "Late Edit"}},
    )
    assert response.status_code == 409


async def test_cancel_application_via_status_patch(
    client: AsyncClient, citizen: dict[str, str]
) -> None:
    application = await create_application(client, citizen)
    response = await client.patch(
        f"/api/applications/{application['id']}",
        headers=citizen["headers"],
        json={"status": "cancelled"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


async def test_unknown_service_type_is_rejected(
    client: AsyncClient, citizen: dict[str, str]
) -> None:
    response = await client.post(
        "/api/applications",
        headers=citizen["headers"],
        json={"service_type": "passport_renewal"},
    )
    assert response.status_code == 422


async def test_application_creation_writes_audit_event(
    client: AsyncClient, citizen: dict[str, str], db: object
) -> None:
    application = await create_application(client, citizen)

    logs = await db["audit_logs"].find(
        {"action": "application.create", "application_id": application["id"]}
    ).to_list(10)
    assert len(logs) == 1
    assert logs[0]["actor_type"] == "user"
    assert logs[0]["actor_id"] == citizen["user_id"]
    assert logs[0]["result"] == "success"


async def test_form_update_and_cancel_write_audit_events(
    client: AsyncClient, citizen: dict[str, str], db: object
) -> None:
    application = await create_application(client, citizen)
    await client.patch(
        f"/api/applications/{application['id']}",
        headers=citizen["headers"],
        json={"form_data": {"full_name": "Audit Person"}},
    )
    await client.delete(
        f"/api/applications/{application['id']}", headers=citizen["headers"]
    )

    actions = await db["audit_logs"].find(
        {"application_id": application["id"]}
    ).to_list(50)
    names = sorted(entry["action"] for entry in actions)
    assert names == ["application.cancel", "application.create", "application.form_updated"]
