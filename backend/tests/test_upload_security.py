"""Upload security tests: type checks, size limits, private download, audit."""

from __future__ import annotations

import io

from bson import ObjectId
from httpx import AsyncClient

from conftest import create_application, jpeg_bytes, pdf_bytes, png_bytes

MAX_SIZE = 5 * 1024 * 1024


async def upload(
    client: AsyncClient,
    auth: dict[str, str],
    application_id: str,
    filename: str,
    content: bytes,
    content_type: str,
    document_type: str = "identity_proof",
):
    return await client.post(
        f"/api/applications/{application_id}/documents",
        headers=auth["headers"],
        data={"document_type": document_type},
        files={"file": (filename, io.BytesIO(content), content_type)},
    )


async def test_valid_png_upload_is_accepted(
    client: AsyncClient, citizen: dict[str, str]
) -> None:
    application = await create_application(client, citizen)
    response = await upload(
        client, citizen, application["id"], "photo.png", png_bytes(), "image/png"
    )
    assert response.status_code == 201
    body = response.json()
    assert body["validation_status"] == "validated"
    assert body["mime_type"] == "image/png"
    assert body["file_size"] == len(png_bytes())
    assert body["document_type"] == "identity_proof"


async def test_valid_jpeg_and_pdf_uploads_are_accepted(
    client: AsyncClient, citizen: dict[str, str]
) -> None:
    application = await create_application(client, citizen)
    jpeg = await upload(
        client, citizen, application["id"], "scan.jpg", jpeg_bytes(), "image/jpeg",
        document_type="address_proof",
    )
    pdf = await upload(
        client, citizen, application["id"], "form.pdf", pdf_bytes(), "application/pdf",
        document_type="income_proof",
    )
    assert jpeg.status_code == 201
    assert pdf.status_code == 201


async def test_disallowed_file_type_is_rejected(
    client: AsyncClient, citizen: dict[str, str]
) -> None:
    application = await create_application(client, citizen)
    response = await upload(
        client,
        citizen,
        application["id"],
        "script.exe",
        b"MZ\x90\x00" + b"\x00" * 32,
        "application/octet-stream",
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


async def test_plain_text_disguised_as_png_is_rejected(
    client: AsyncClient, citizen: dict[str, str]
) -> None:
    application = await create_application(client, citizen)
    response = await upload(
        client,
        citizen,
        application["id"],
        "fake.png",
        b"this is definitely not a png",
        "image/png",
    )
    assert response.status_code == 400


async def test_content_type_mismatch_is_rejected(
    client: AsyncClient, citizen: dict[str, str]
) -> None:
    application = await create_application(client, citizen)
    response = await upload(
        client, citizen, application["id"], "mismatch.png", pdf_bytes(), "image/png"
    )
    assert response.status_code == 400


async def test_oversized_file_is_rejected(
    client: AsyncClient, citizen: dict[str, str]
) -> None:
    application = await create_application(client, citizen)
    oversized = b"%PDF-" + b"\x00" * (MAX_SIZE + 1)
    response = await upload(
        client, citizen, application["id"], "big.pdf", oversized, "application/pdf"
    )
    assert response.status_code == 413
    assert "too large" in response.json()["detail"]


async def test_unknown_document_type_is_rejected(
    client: AsyncClient, citizen: dict[str, str]
) -> None:
    application = await create_application(client, citizen)
    response = await client.post(
        f"/api/applications/{application['id']}/documents",
        headers=citizen["headers"],
        data={"document_type": "bank_statement"},
        files={"file": ("x.png", io.BytesIO(png_bytes()), "image/png")},
    )
    assert response.status_code == 422


async def test_upload_to_other_users_application_is_denied(
    client: AsyncClient, citizen: dict[str, str], other_citizen: dict[str, str]
) -> None:
    application = await create_application(client, citizen)
    response = await upload(
        client, other_citizen, application["id"], "x.png", png_bytes(), "image/png"
    )
    assert response.status_code == 404


async def test_private_download_returns_original_bytes(
    client: AsyncClient, citizen: dict[str, str]
) -> None:
    application = await create_application(client, citizen)
    content = png_bytes(128)
    created = await upload(
        client, citizen, application["id"], "citizenship.png", content, "image/png"
    )
    document_id = created.json()["id"]

    download = await client.get(
        f"/api/documents/{document_id}/download", headers=citizen["headers"]
    )
    assert download.status_code == 200
    assert download.content == content
    assert download.headers["content-type"].startswith("image/png")
    assert download.headers["x-content-type-options"] == "nosniff"
    assert "attachment" in download.headers["content-disposition"]
    assert "citizenship.png" in download.headers["content-disposition"]


async def test_download_requires_authentication(
    client: AsyncClient, citizen: dict[str, str]
) -> None:
    application = await create_application(client, citizen)
    created = await upload(
        client, citizen, application["id"], "x.png", png_bytes(), "image/png"
    )
    document_id = created.json()["id"]

    anonymous = await client.get(f"/api/documents/{document_id}/download")
    assert anonymous.status_code == 401


async def test_storage_key_is_random_and_not_user_controlled(
    client: AsyncClient, citizen: dict[str, str], db: object
) -> None:
    application = await create_application(client, citizen)
    created = await upload(
        client,
        citizen,
        application["id"],
        "../../evil.png",
        png_bytes(),
        "image/png",
    )
    assert created.status_code == 201
    document_id = created.json()["id"]

    record = await db["documents"].find_one({"_id": ObjectId(document_id)})
    assert record is not None
    storage_key = record["storage_key"]
    assert storage_key.startswith(f"{application['id']}/")
    assert ".." not in storage_key
    assert "evil" not in storage_key
    assert storage_key.endswith(".png")
    assert record["safe_filename"] == "evil.png"


async def test_delete_document_removes_it(
    client: AsyncClient, citizen: dict[str, str], db: object
) -> None:
    application = await create_application(client, citizen)
    created = await upload(
        client, citizen, application["id"], "temp.png", png_bytes(), "image/png"
    )
    document_id = created.json()["id"]

    delete = await client.delete(
        f"/api/documents/{document_id}", headers=citizen["headers"]
    )
    assert delete.status_code == 200

    listing = await client.get(
        f"/api/applications/{application['id']}/documents",
        headers=citizen["headers"],
    )
    assert listing.json() == []
    assert await db["documents"].count_documents({}) == 0

    gone = await client.get(
        f"/api/documents/{document_id}/download", headers=citizen["headers"]
    )
    assert gone.status_code == 404


async def test_upload_writes_audit_event_with_hash(
    client: AsyncClient, citizen: dict[str, str], db: object
) -> None:
    application = await create_application(client, citizen)
    await upload(client, citizen, application["id"], "audit.png", png_bytes(), "image/png")

    logs = await db["audit_logs"].find(
        {"action": "document.upload", "application_id": application["id"]}
    ).to_list(10)
    assert len(logs) == 1
    assert logs[0]["metadata"]["document_type"] == "identity_proof"
    assert len(logs[0]["metadata"]["file_hash"]) == 64
    assert logs[0]["result"] == "success"


async def test_upload_moves_application_status_to_documents_pending(
    client: AsyncClient, citizen: dict[str, str]
) -> None:
    application = await create_application(client, citizen)
    await upload(
        client, citizen, application["id"], "a.png", png_bytes(), "image/png",
        document_type="identity_proof",
    )

    refreshed = await client.get(
        f"/api/applications/{application['id']}", headers=citizen["headers"]
    )
    body = refreshed.json()
    assert body["status"] == "documents_pending"
    assert body["document_count"] == 1
    assert body["progress_percent"] > 0
