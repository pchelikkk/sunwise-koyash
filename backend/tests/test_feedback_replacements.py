from fastapi.testclient import TestClient

from app.main import app


def _recommendation_payload() -> dict:
    return {
        "skin_type": "combination",
        "concerns": ["acne", "sebum"],
        "budget": "balanced",
        "excluded_ingredients": ["fragrance"],
        "custom_restrictions": [],
        "experience": "basic",
        "values": ["comfort", "price_quality"],
        "anonymous_id": "test-feedback-anon",
    }


def _create_recommendation(client: TestClient) -> str:
    response = client.post("/api/v1/recommendations", json=_recommendation_payload())
    assert response.status_code == 200
    return response.json()["recommendation_id"]


def test_feedback_returns_replacement_candidates() -> None:
    with TestClient(app) as client:
        recommendation_id = _create_recommendation(client)

        response = client.post(
            f"/api/v1/recommendations/{recommendation_id}/feedback",
            json={
                "product_external_id": "cleanser_001",
                "reason": "too_expensive",
                "comment": "Хочу дешевле",
                "anonymous_id": "test-feedback-anon",
            },
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["feedback"]["recommendation_id"] == recommendation_id
    assert payload["feedback"]["product_external_id"] == "cleanser_001"
    assert payload["feedback"]["reason"] == "too_expensive"
    assert payload["replacement_strategy"] == "cheaper_same_step"
    assert payload["replacement_session_id"]
    assert payload["replacement_candidates"]

    first_candidate = payload["replacement_candidates"][0]
    assert first_candidate["product"]["routine_step"] == "cleanser"
    assert first_candidate["product"]["external_id"] != "cleanser_001"
    assert first_candidate["why_better"]
    assert first_candidate["strategy_reason"]


def test_replacements_can_be_listed_after_feedback() -> None:
    with TestClient(app) as client:
        recommendation_id = _create_recommendation(client)

        feedback_response = client.post(
            f"/api/v1/recommendations/{recommendation_id}/feedback",
            json={
                "product_external_id": "cleanser_001",
                "reason": "too_expensive",
                "anonymous_id": "test-feedback-anon",
            },
        )
        assert feedback_response.status_code == 200

        list_response = client.get(
            f"/api/v1/recommendations/{recommendation_id}/replacements",
            params={"anonymous_id": "test-feedback-anon"},
        )

    assert list_response.status_code == 200

    payload = list_response.json()
    assert payload["replacements"]
    assert payload["replacements"][0]["recommendation_id"] == recommendation_id
    assert payload["replacements"][0]["candidates"]


def test_replacement_candidate_is_applied_to_the_stored_routine() -> None:
    with TestClient(app) as client:
        recommendation_id = _create_recommendation(client)

        feedback_response = client.post(
            f"/api/v1/recommendations/{recommendation_id}/feedback",
            json={
                "product_external_id": "cleanser_001",
                "reason": "too_expensive",
                "anonymous_id": "test-feedback-anon",
            },
        )
        assert feedback_response.status_code == 200

        feedback_payload = feedback_response.json()
        replacement_session_id = feedback_payload["replacement_session_id"]
        candidate_id = feedback_payload["replacement_candidates"][0]["product"]["external_id"]
        original_id = feedback_payload["product_external_id"]

        select_response = client.post(
            f"/api/v1/recommendations/{recommendation_id}/replacements/{replacement_session_id}/select",
            json={
                "product_external_id": candidate_id,
                "anonymous_id": "test-feedback-anon",
            },
        )

        duplicate_response = client.post(
            f"/api/v1/recommendations/{recommendation_id}/replacements/{replacement_session_id}/select",
            json={
                "product_external_id": candidate_id,
                "anonymous_id": "test-feedback-anon",
            },
        )

        refreshed_response = client.get(
            f"/api/v1/recommendations/{recommendation_id}",
            params={"anonymous_id": "test-feedback-anon"},
        )

    assert select_response.status_code == 200
    assert duplicate_response.status_code == 409
    assert refreshed_response.status_code == 200

    payload = select_response.json()
    assert payload["replacement_session_id"] == replacement_session_id
    assert payload["selected_product_external_id"] == candidate_id
    assert payload["status"] == "selected"
    selected_items = [
        *payload["routine"]["morning"],
        *payload["routine"]["evening"],
    ]
    refreshed = refreshed_response.json()
    refreshed_items = [
        *refreshed["routine"]["morning"],
        *refreshed["routine"]["evening"],
    ]
    assert candidate_id in {
        item["product"]["external_id"] for item in selected_items
    }
    assert original_id not in {
        item["product"]["external_id"] for item in selected_items
    }
    assert payload["routine"] == refreshed["routine"]
    assert payload["total_price_rub"] == refreshed["total_price_rub"]
    unique_products = {
        item["product"]["external_id"]: item["product"] for item in refreshed_items
    }
    assert refreshed["total_price_rub"] == sum(
        product["price_rub"] for product in unique_products.values()
    )


def test_feedback_reports_when_no_safe_replacement_exists(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.feedback_service.build_replacement_candidates",
        lambda **kwargs: [],
    )

    with TestClient(app) as client:
        recommendation_id = _create_recommendation(client)
        response = client.post(
            f"/api/v1/recommendations/{recommendation_id}/feedback",
            json={
                "product_external_id": "cleanser_001",
                "reason": "too_expensive",
                "anonymous_id": "test-feedback-anon",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["replacement_candidates"] == []
    assert payload["replacement_status"] == "not_found"
    assert "не нашли безопасную замену" in payload["replacement_message"].lower()


def test_feedback_unknown_recommendation_returns_404() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/recommendations/000000000000000000000000/feedback",
            json={
                "product_external_id": "cleanser_001",
                "reason": "too_expensive",
            },
        )

    assert response.status_code == 404


def test_feedback_rejects_catalog_product_outside_recommendation() -> None:
    with TestClient(app) as client:
        recommendation_response = client.post(
            "/api/v1/recommendations",
            json=_recommendation_payload(),
        )
        assert recommendation_response.status_code == 200
        recommendation = recommendation_response.json()

        routine_items = [
            *recommendation["routine"]["morning"],
            *recommendation["routine"]["evening"],
        ]
        recommended_product_ids = {
            item["product"]["external_id"] for item in routine_items
        }

        catalog_response = client.get("/api/v1/products")
        assert catalog_response.status_code == 200
        outside_product = next(
            product
            for product in catalog_response.json()
            if product["external_id"] not in recommended_product_ids
        )

        response = client.post(
            f"/api/v1/recommendations/{recommendation['recommendation_id']}/feedback",
            json={
                "product_external_id": outside_product["external_id"],
                "reason": "other",
                "anonymous_id": "test-feedback-anon",
            },
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product is not part of this recommendation"
