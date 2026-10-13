from fastapi.testclient import TestClient

from app.main import app


def _payload() -> dict:
    return {
        "age": 19,
        "skin_type": "combination",
        "concerns": ["acne", "sebum"],
        "budget": "balanced",
        "excluded_ingredients": ["fragrance"],
        "custom_restrictions": [],
        "experience": "guided",
        "values": ["comfort", "price", "quality"],
        "anonymous_id": "test-anon",
    }


def test_recommendation_can_be_created() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/recommendations", json=_payload())

    assert response.status_code == 200

    payload = response.json()
    assert payload["recommendation_id"]
    assert payload["algorithm_version"] == "rule-based-v2"
    assert payload["routine"]["morning"]
    assert payload["routine"]["evening"]
    assert any(
        item["routine_step"] == "moisturizer"
        for item in payload["routine"]["morning"]
    )
    assert payload["total_price_rub"] > 0
    assert payload["filter_summary"]["total_products"] >= 8


def test_recommendation_items_have_explanations_and_scores() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/recommendations", json=_payload())

    assert response.status_code == 200

    payload = response.json()
    items = payload["routine"]["morning"] + payload["routine"]["evening"]

    assert items

    for item in items:
        assert item["score"] > 0
        assert item["why_here"]
        assert item["budget_reason"]
        assert item["safety_note"]
        assert item["how_to_use"]
        assert item["score_breakdown"]["total"] == item["score"]
        assert item["llm_ready_context"]["tone"]
        assert item["llm_ready_context"]["user_profile"]["age"] == 19


def test_recommendation_excludes_fragrance_product() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/recommendations", json=_payload())

    assert response.status_code == 200

    payload = response.json()
    items = payload["routine"]["morning"] + payload["routine"]["evening"]
    external_ids = {item["product"]["external_id"] for item in items}

    assert "spf_002" not in external_ids
    assert payload["filter_summary"]["filter_reasons"]["excluded_ingredient"] >= 1
    coverage = payload["filter_summary"]["restriction_coverage"]
    assert coverage["requested_restrictions"] == ["fragrance"]
    assert coverage["matched_restrictions"] == ["fragrance"]
    assert coverage["unmatched_restrictions"] == []
    assert coverage["matches"][0]["restriction"] == "fragrance"
    assert coverage["matches"][0]["matched_product_count"] >= 1


def test_recommendation_reports_unmatched_custom_restriction() -> None:
    payload = {
        **_payload(),
        "excluded_ingredients": [],
        "custom_restrictions": [
            "niacinamide",
            "$ingredient.not-present-in-catalog",
        ],
    }

    with TestClient(app) as client:
        response = client.post("/api/v1/recommendations", json=payload)

    assert response.status_code == 200
    result = response.json()
    coverage = result["filter_summary"]["restriction_coverage"]

    assert coverage["requested_restrictions"] == [
        "niacinamide",
        "$ingredient.not-present-in-catalog",
    ]
    assert coverage["matched_restrictions"] == ["niacinamide"]
    assert coverage["unmatched_restrictions"] == [
        "$ingredient.not-present-in-catalog"
    ]
    matches = {
        item["restriction"]: item["matched_product_count"]
        for item in coverage["matches"]
    }
    assert matches["niacinamide"] >= 1
    assert matches["$ingredient.not-present-in-catalog"] == 0
    assert result["filter_summary"]["filter_reasons"]["excluded_ingredient"] >= 1

    with TestClient(app) as client:
        loaded_response = client.get(
            f"/api/v1/recommendations/{result['recommendation_id']}",
            params={"anonymous_id": "test-anon"},
        )

    assert loaded_response.status_code == 200
    assert (
        loaded_response.json()["filter_summary"]["restriction_coverage"]
        == coverage
    )


def test_recommendation_can_be_loaded_by_id() -> None:
    with TestClient(app) as client:
        create_response = client.post("/api/v1/recommendations", json=_payload())

    assert create_response.status_code == 200
    recommendation_id = create_response.json()["recommendation_id"]

    with TestClient(app) as client:
        get_response = client.get(
            f"/api/v1/recommendations/{recommendation_id}",
            params={"anonymous_id": "test-anon"},
        )

    assert get_response.status_code == 200
    payload = get_response.json()

    assert payload["recommendation_id"] == recommendation_id
    assert payload["routine"]["morning"]
    assert payload["routine"]["evening"]


def test_anonymous_recommendation_rejects_a_different_browser_identity() -> None:
    with TestClient(app) as client:
        create_response = client.post("/api/v1/recommendations", json=_payload())
        recommendation_id = create_response.json()["recommendation_id"]
        missing_identity = client.get(f"/api/v1/recommendations/{recommendation_id}")
        wrong_identity = client.get(
            f"/api/v1/recommendations/{recommendation_id}",
            params={"anonymous_id": "another-browser"},
        )

    assert missing_identity.status_code == 404
    assert wrong_identity.status_code == 404


def test_reactivity_and_design_values_are_normalized() -> None:
    payload = {
        **_payload(),
        "concerns": ["reactivity", "unknown"],
        "excluded_ingredients": ["unknown", "none", "fragrance"],
        "experience": "guided",
        "values": ["price", "quality", "simple_routine", "unknown"],
    }

    with TestClient(app) as client:
        response = client.post("/api/v1/recommendations", json=payload)

    assert response.status_code == 200
    result = response.json()
    items = result["routine"]["morning"] + result["routine"]["evening"]

    assert items
    assert all(item["score"] > 0 for item in items)


def test_unknown_recommendation_returns_404() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/recommendations/000000000000000000000000")

    assert response.status_code == 404
