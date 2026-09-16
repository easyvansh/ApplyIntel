from fastapi.testclient import TestClient


def test_legacy_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert response.headers["X-Request-ID"]


def test_liveness_endpoint(client: TestClient) -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness_checks_database_and_echoes_request_id(client: TestClient) -> None:
    response = client.get("/health/ready", headers={"X-Request-ID": "health-check-123"})

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "connected"}
    assert response.headers["X-Request-ID"] == "health-check-123"
