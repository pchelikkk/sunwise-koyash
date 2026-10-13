from fastapi.testclient import TestClient

from app.main import app


def test_restriction_suggestions_are_available() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/restrictions/suggestions")

    assert response.status_code == 200
    payload = response.json()

    keys = {item["canonical_key"] for item in payload["suggestions"]}
    assert "fragrance" in keys
    assert "alcohol" in keys
    assert "essential_oils" in keys
    assert "none" in keys


def test_custom_restriction_normalizes_known_alias() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/restrictions/custom",
            json={"value": "спирт", "anonymous_id": "test-anon"},
        )

    assert response.status_code == 200
    payload = response.json()

    assert payload["raw_value"] == "спирт"
    assert payload["normalized_key"] == "alcohol"
    assert payload["display_name"] == "Спирт"
    assert payload["status"] == "approved"
    assert payload["added_to_popular"] is True


def test_custom_restriction_unknown_value_is_pending() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/restrictions/custom",
            json={"value": "мой редкий ингредиент", "anonymous_id": "test-anon"},
        )

    assert response.status_code == 200
    payload = response.json()

    assert payload["normalized_key"].startswith("custom_")
    assert payload["status"] == "pending"
    assert payload["added_to_popular"] is False
