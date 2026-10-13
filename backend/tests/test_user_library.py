from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def _register(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"library-{uuid4().hex}@example.com",
            "password": "StrongPassword123!",
            "full_name": "Library User",
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def test_favorites_are_idempotent_and_private() -> None:
    with TestClient(app) as client:
        token = _register(client)
        headers = {"Authorization": f"Bearer {token}"}

        first = client.put(
            "/api/v1/users/me/favorites/cleanser_001",
            headers=headers,
        )
        second = client.put(
            "/api/v1/users/me/favorites/cleanser_001",
            headers=headers,
        )
        listed = client.get("/api/v1/users/me/favorites", headers=headers)

        assert first.status_code == 200
        assert second.status_code == 200
        assert listed.status_code == 200
        assert listed.json()["total"] == 1
        assert listed.json()["items"][0]["product"]["external_id"] == "cleanser_001"

        removed = client.delete(
            "/api/v1/users/me/favorites/cleanser_001",
            headers=headers,
        )
        empty = client.get("/api/v1/users/me/favorites", headers=headers)

    assert removed.status_code == 204
    assert empty.json() == {"items": [], "total": 0}


def test_favorite_requires_auth_and_existing_product() -> None:
    with TestClient(app) as client:
        no_auth = client.get("/api/v1/users/me/favorites")
        token = _register(client)
        unknown = client.put(
            "/api/v1/users/me/favorites/not-a-product",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert no_auth.status_code == 401
    assert unknown.status_code == 404


def test_cosmetic_bag_is_idempotent_private_and_clearable() -> None:
    with TestClient(app) as client:
        token = _register(client)
        headers = {"Authorization": f"Bearer {token}"}

        first = client.put(
            "/api/v1/users/me/cosmetic-bag/cleanser_001",
            headers=headers,
        )
        second = client.put(
            "/api/v1/users/me/cosmetic-bag/cleanser_001",
            headers=headers,
        )
        listed = client.get("/api/v1/users/me/cosmetic-bag", headers=headers)

        assert first.status_code == 200
        assert second.status_code == 200
        assert listed.status_code == 200
        assert listed.json()["total"] == 1
        assert listed.json()["items"][0]["product"]["external_id"] == "cleanser_001"

        cleared = client.delete("/api/v1/users/me/cosmetic-bag", headers=headers)
        empty = client.get("/api/v1/users/me/cosmetic-bag", headers=headers)

    assert cleared.status_code == 204
    assert empty.json() == {"items": [], "total": 0}


def test_cosmetic_bag_requires_auth_and_existing_product() -> None:
    with TestClient(app) as client:
        no_auth = client.get("/api/v1/users/me/cosmetic-bag")
        token = _register(client)
        unknown = client.put(
            "/api/v1/users/me/cosmetic-bag/not-a-product",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert no_auth.status_code == 401
    assert unknown.status_code == 404


def test_recommendation_history_uses_owned_server_sessions() -> None:
    with TestClient(app) as client:
        token = _register(client)
        headers = {"Authorization": f"Bearer {token}"}
        created = client.post(
            "/api/v1/recommendations",
            headers=headers,
            json={
                "skin_type": "combination",
                "concerns": ["acne"],
                "budget": "balanced",
            },
        )
        assert created.status_code == 200

        history = client.get(
            "/api/v1/users/me/recommendations",
            headers=headers,
        )

    assert history.status_code == 200
    payload = history.json()
    assert payload["total"] == 1
    assert payload["items"][0]["recommendation_id"] == created.json()["recommendation_id"]
    assert payload["items"][0]["routine"] == created.json()["routine"]
