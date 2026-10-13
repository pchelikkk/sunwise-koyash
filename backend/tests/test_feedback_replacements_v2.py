from typing import Any

from fastapi.testclient import TestClient

from app.main import app


def _recommendation(client: TestClient) -> dict[str, Any]:
    response = client.post(
        "/api/v1/recommendations",
        json={
            "age": 24,
            "skin_type": "combination",
            "concerns": ["sebum", "acne"],
            "budget": "balanced",
            "excluded_ingredients": ["fragrance"],
            "custom_restrictions": [],
            "experience": "guided",
            "values": ["comfort", "price_quality"],
            "anonymous_id": "replacement-v2-test",
        },
    )

    assert response.status_code == 200
    return response.json()


def _items(recommendation: dict[str, Any]) -> list[dict[str, Any]]:
    routine = recommendation["routine"]
    return [*routine.get("morning", []), *routine.get("evening", [])]


def _submit_feedback(
    client: TestClient,
    recommendation: dict[str, Any],
    reason: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    item = _items(recommendation)[0]
    product = item["product"]

    response = client.post(
        f"/api/v1/recommendations/{recommendation['recommendation_id']}/feedback",
        json={
            "product_external_id": product["external_id"],
            "reason": reason,
            "comment": "test feedback",
            "anonymous_id": "replacement-v2-test",
        },
    )

    assert response.status_code == 200
    return item, response.json()


def test_replacement_candidates_do_not_include_original_product() -> None:
    with TestClient(app) as client:
        recommendation = _recommendation(client)
        original_item, payload = _submit_feedback(client, recommendation, "other")

    original_id = original_item["product"]["external_id"]
    candidates = payload["replacement_candidates"]

    assert candidates
    assert all(candidate["product"]["external_id"] != original_id for candidate in candidates)


def test_too_expensive_prioritizes_cheaper_candidate_when_available() -> None:
    with TestClient(app) as client:
        recommendation = _recommendation(client)
        original_item, payload = _submit_feedback(client, recommendation, "too_expensive")

    original_price = original_item["product"]["price_rub"]
    candidates = payload["replacement_candidates"]

    assert candidates

    cheaper_candidates = [
        candidate for candidate in candidates
        if candidate["product"]["price_rub"] < original_price
    ]

    if cheaper_candidates:
        assert candidates[0]["product"]["price_rub"] < original_price

    assert (
        "дешев" in candidates[0]["why_better"].lower()
        or candidates[0]["reason"] == "too_expensive"
    )


def test_dislikes_brand_prioritizes_another_brand_when_available() -> None:
    with TestClient(app) as client:
        recommendation = _recommendation(client)
        original_item, payload = _submit_feedback(client, recommendation, "dislikes_brand")

    original_brand = original_item["product"]["brand"]
    candidates = payload["replacement_candidates"]

    assert candidates

    different_brand_candidates = [
        candidate for candidate in candidates
        if candidate["product"]["brand"] != original_brand
    ]

    if different_brand_candidates:
        assert candidates[0]["product"]["brand"] != original_brand


def test_composition_concern_returns_explanatory_safer_alternative() -> None:
    with TestClient(app) as client:
        recommendation = _recommendation(client)
        _, payload = _submit_feedback(client, recommendation, "composition_concern")

    candidates = payload["replacement_candidates"]

    assert candidates
    assert candidates[0]["why_better"]
    assert candidates[0]["replacement_reason"]


def test_replacement_sessions_can_be_listed_and_selected() -> None:
    with TestClient(app) as client:
        recommendation = _recommendation(client)
        _, payload = _submit_feedback(client, recommendation, "texture_not_suitable")

        list_response = client.get(
            f"/api/v1/recommendations/{recommendation['recommendation_id']}/replacements",
            params={"anonymous_id": "replacement-v2-test"},
        )

        assert list_response.status_code == 200
        sessions = list_response.json()
        assert sessions

        candidate_id = payload["replacement_candidates"][0]["product"]["external_id"]

        select_response = client.post(
            f"/api/v1/recommendations/{recommendation['recommendation_id']}/replacements/{payload['replacement_session_id']}/select",
            json={
                "product_external_id": candidate_id,
                "anonymous_id": "replacement-v2-test",
            },
        )

    assert select_response.status_code == 200
    selected = select_response.json()
    assert selected["selected_product_external_id"] == candidate_id
    assert selected["status"] == "selected"


def test_replacement_selection_rejects_product_outside_candidates() -> None:
    with TestClient(app) as client:
        recommendation = _recommendation(client)
        _, payload = _submit_feedback(client, recommendation, "too_many_steps")

        response = client.post(
            f"/api/v1/recommendations/{recommendation['recommendation_id']}/replacements/{payload['replacement_session_id']}/select",
            json={
                "product_external_id": "not-a-candidate",
                "anonymous_id": "replacement-v2-test",
            },
        )

    assert response.status_code == 400
