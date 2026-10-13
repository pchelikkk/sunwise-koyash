from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient

from app.core.config import get_settings
from app.main import app


def _register(client: TestClient) -> tuple[str, dict]:
    email = f"analytics-{uuid4().hex}@example.com"
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "Analytics User",
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"], response.json()["user"]


def _set_role(email: str, role: str) -> None:
    settings = get_settings()
    client = MongoClient(
        settings.mongo_uri,
        uuidRepresentation="standard",
        serverSelectionTimeoutMS=5000,
    )
    try:
        result = client[settings.mongo_db_name]["users"].update_one(
            {"email": email.lower()},
            {"$set": {"role": role}},
        )
        assert result.matched_count == 1
    finally:
        client.close()


def test_public_analytics_event_can_be_recorded_anonymously() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/analytics/events",
            json={
                "event_type": "product_viewed",
                "anonymous_id": "analytics-test",
                "product_external_id": "cleanser_001",
                "metadata": {"source": "test"},
            },
        )

    assert response.status_code == 201
    assert response.json()["status"] == "recorded"


@pytest.mark.parametrize(
    "event_type",
    [
        "favorite_added",
        "favorite_removed",
        "cosmetic_bag_added",
        "cosmetic_bag_removed",
        "recommendation_shared",
        "store_opened",
    ],
)
def test_public_product_collection_events_are_allowed(event_type: str) -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/analytics/events",
            json={
                "event_type": event_type,
                "anonymous_id": "collection-event-test",
                "product_external_id": "product_001",
                "metadata": {"surface": "test"},
            },
        )

    assert response.status_code == 201


def test_public_analytics_rejects_server_owned_event_type() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/analytics/events",
            json={
                "event_type": "feedback_submitted",
                "metadata": {"source": "spoofed"},
            },
        )

    assert response.status_code == 422


def test_public_analytics_rejects_user_id_spoofing() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/analytics/events",
            json={
                "event_type": "result_viewed",
                "user_id": "forged-user-id",
                "metadata": {},
            },
        )

    assert response.status_code == 422


def test_admin_summary_without_token_returns_401() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/admin/analytics/summary")

    assert response.status_code == 401


def test_admin_summary_for_regular_user_returns_403() -> None:
    with TestClient(app) as client:
        token, _ = _register(client)
        response = client.get(
            "/api/v1/admin/analytics/summary",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_admin_summary_for_admin_returns_200() -> None:
    with TestClient(app) as client:
        token, user = _register(client)
        _set_role(user["email"], "admin")

        response = client.get(
            "/api/v1/admin/analytics/summary",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert "total_events" in payload
    assert "events_by_type" in payload
    assert "recent_events" in payload


def test_admin_summary_is_hidden_from_openapi() -> None:
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    assert "/api/v1/admin/analytics/summary" not in schema["paths"]
