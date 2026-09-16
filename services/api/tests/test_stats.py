from fastapi.testclient import TestClient


def test_stats_returns_expected_shape_and_values(
    client: TestClient, application_payload: dict[str, str | None]
) -> None:
    client.post("/applications", json=application_payload)
    client.post(
        "/applications",
        json={**application_payload, "company": "Globex", "status": "interview"},
    )
    client.post(
        "/applications",
        json={
            **application_payload,
            "company": "Initech",
            "status": "offer",
            "next_action_date": None,
        },
    )

    response = client.get("/stats")

    assert response.status_code == 200
    assert response.json() == {
        "total": 3,
        "counts": {"applied": 1, "interview": 1, "offer": 1},
        "response_rate": 0.6667,
        "due_today": 2,
        "saved_jobs": 0,
        "interviews": 1,
    }
