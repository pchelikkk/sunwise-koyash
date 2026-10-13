from fastapi.testclient import TestClient

from app.main import app


def _payload() -> dict:
    return {
        "skin_type": "combination",
        "concerns": ["acne", "sebum"],
        "budget": "balanced",
        "excluded_ingredients": ["fragrance"],
        "custom_restrictions": [],
        "experience": "beginner",
        "values": ["comfort", "price_quality"],
        "anonymous_id": "contract-test-anon",
    }

def _selected_external_ids(payload: dict) -> set[str]:
    items = payload["routine"]["morning"] + payload["routine"]["evening"]
    return {item["product"]["external_id"] for item in items}

def test_recommendation_selection_is_stable_for_same_input() -> None:
    with TestClient(app) as client:
        first = client.post("/api/v1/recommendations", json=_payload())
        second = client.post("/api/v1/recommendations", json=_payload())
        assert first.status_code == 200
        assert second.status_code == 200
        first_payload = first.json()
        second_payload = second.json()
        assert _selected_external_ids(first_payload) == _selected_external_ids(second_payload)
        assert first_payload["total_price_rub"] == second_payload["total_price_rub"]

def test_feedback_rejects_invalid_reason() -> None:
    with TestClient(app) as client:
        create = client.post("/api/v1/recommendations", json=_payload())
        assert create.status_code == 200
        recommendation_id = create.json()["recommendation_id"]
        response = client.post(
            f"/api/v1/recommendations/{recommendation_id}/feedback",
            json={
                "product_external_id": "cleanser_001",
                "reason": "not_a_real_reason",
            },
        )
        assert response.status_code == 422
