from fastapi.testclient import TestClient


def create_application(client: TestClient, payload: dict[str, str | None]) -> dict:
    response = client.post("/applications", json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_and_list_application(
    client: TestClient, application_payload: dict[str, str | None]
) -> None:
    created = create_application(client, application_payload)

    response = client.get("/applications")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == created["id"]
    assert response.json()["items"][0]["company"] == "Acme Labs"


def test_searches_company_and_role(
    client: TestClient, application_payload: dict[str, str | None]
) -> None:
    create_application(client, application_payload)
    second = {**application_payload, "company": "Globex", "role": "Data Analyst"}
    create_application(client, second)

    by_company = client.get("/applications", params={"q": "acme"})
    by_role = client.get("/applications", params={"q": "analyst"})

    assert by_company.json()["total"] == 1
    assert by_company.json()["items"][0]["company"] == "Acme Labs"
    assert by_role.json()["total"] == 1
    assert by_role.json()["items"][0]["company"] == "Globex"


def test_filters_by_status_and_paginates(
    client: TestClient, application_payload: dict[str, str | None]
) -> None:
    create_application(client, application_payload)
    create_application(client, {**application_payload, "company": "Globex", "status": "saved"})
    create_application(client, {**application_payload, "company": "Initech"})

    filtered = client.get("/applications", params={"status": "saved"})
    first_page = client.get("/applications", params={"limit": 1, "offset": 0})
    second_page = client.get("/applications", params={"limit": 1, "offset": 1})

    assert filtered.json()["total"] == 1
    assert filtered.json()["items"][0]["status"] == "saved"
    assert first_page.json()["total"] == 3
    assert len(first_page.json()["items"]) == 1
    assert second_page.json()["total"] == 3
    assert first_page.json()["items"][0]["id"] != second_page.json()["items"][0]["id"]


def test_updates_application_status(
    client: TestClient, application_payload: dict[str, str | None]
) -> None:
    created = create_application(client, application_payload)

    response = client.patch(f"/applications/{created['id']}", json={"status": "interview"})

    assert response.status_code == 200
    assert response.json()["status"] == "interview"


def test_soft_deletes_and_restores_application(
    client: TestClient, application_payload: dict[str, str | None]
) -> None:
    created = create_application(client, application_payload)

    deleted = client.delete(f"/applications/{created['id']}")
    active_list = client.get("/applications")
    deleted_list = client.get("/applications", params={"include_deleted": True})
    restored = client.post(f"/applications/{created['id']}/restore")

    assert deleted.status_code == 200
    assert active_list.json()["total"] == 0
    assert deleted_list.json()["total"] == 1
    assert restored.status_code == 200
    assert client.get("/applications").json()["total"] == 1


def test_missing_application_returns_structured_error(client: TestClient) -> None:
    response = client.patch(
        "/applications/9999",
        json={"status": "offer"},
        headers={"X-Request-ID": "missing-app-123"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "APPLICATION_NOT_FOUND",
            "message": "Application 9999 was not found.",
            "request_id": "missing-app-123",
        }
    }
    assert response.headers["X-Request-ID"] == "missing-app-123"


def test_invalid_application_input_keeps_fastapi_validation_shape(client: TestClient) -> None:
    response = client.post("/applications", json={"company": ""})

    assert response.status_code == 422
    assert "detail" in response.json()
