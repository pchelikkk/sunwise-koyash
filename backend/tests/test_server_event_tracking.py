from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pymongo import DESCENDING, MongoClient

from app.core.config import get_settings
from app.core.enums import AnalyticsEventType
from app.main import app
from app.services.event_tracking_service import EventTrackingService


def _register(client: TestClient) -> tuple[str, dict]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"events-{uuid4().hex}@example.com",
            "password": "StrongPassword123!",
            "full_name": "Event Test User",
            "anonymous_id": f"anon-{uuid4().hex}",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    return payload["access_token"], payload["user"]


def _recommendation_payload(anonymous_id: str) -> dict:
    return {
        "age": 24,
        "skin_type": "combination",
        "concerns": ["sebum", "acne"],
        "budget": "balanced",
        "excluded_ingredients": ["fragrance"],
        "custom_restrictions": [],
        "experience": "guided",
        "values": ["comfort", "price_quality"],
        "anonymous_id": anonymous_id,
    }


def _find_event(query: dict) -> dict | None:
    settings = get_settings()
    client = MongoClient(
        settings.mongo_uri,
        uuidRepresentation="standard",
        serverSelectionTimeoutMS=5000,
    )
    try:
        return client[settings.mongo_db_name]["analytics_events"].find_one(
            query,
            sort=[("created_at", DESCENDING)],
        )
    finally:
        client.close()


def test_registration_is_recorded_as_server_event_without_email_metadata() -> None:
    with TestClient(app) as client:
        _, user = _register(client)

    event = _find_event(
        {
            "event_type": AnalyticsEventType.REGISTRATION_COMPLETED.value,
            "event_source": "server",
            "user_id": user["user_id"],
        }
    )

    assert event is not None
    assert event["metadata"]["name_provided"] is True
    assert "email" not in event["metadata"]
    assert "password" not in event["metadata"]


def test_authenticated_recommendation_records_questionnaire_and_result_events() -> None:
    with TestClient(app) as client:
        token, user = _register(client)
        response = client.post(
            "/api/v1/recommendations",
            headers={"Authorization": f"Bearer {token}"},
            json=_recommendation_payload(user["anonymous_id"]),
        )

    assert response.status_code == 200
    recommendation_id = response.json()["recommendation_id"]

    questionnaire_event = _find_event(
        {
            "event_type": AnalyticsEventType.QUESTIONNAIRE_COMPLETED.value,
            "event_source": "server",
            "recommendation_id": recommendation_id,
        }
    )
    recommendation_event = _find_event(
        {
            "event_type": AnalyticsEventType.RECOMMENDATION_GENERATED.value,
            "event_source": "server",
            "recommendation_id": recommendation_id,
        }
    )

    assert questionnaire_event is not None
    assert questionnaire_event["user_id"] == user["user_id"]
    assert questionnaire_event["metadata"]["skin_type"] == "combination"
    assert recommendation_event is not None
    assert recommendation_event["metadata"]["routine_product_count"] >= 1
    assert recommendation_event["metadata"]["product_external_ids"]


def test_feedback_generation_and_selection_are_recorded_server_side() -> None:
    with TestClient(app) as client:
        token, user = _register(client)
        recommendation_response = client.post(
            "/api/v1/recommendations",
            headers={"Authorization": f"Bearer {token}"},
            json=_recommendation_payload(user["anonymous_id"]),
        )
        assert recommendation_response.status_code == 200
        recommendation = recommendation_response.json()
        original = recommendation["routine"]["morning"][0]["product"]

        feedback_response = client.post(
            f"/api/v1/recommendations/{recommendation['recommendation_id']}/feedback",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "product_external_id": original["external_id"],
                "reason": "dislikes_brand",
                "comment": "This comment must not enter analytics metadata",
                "anonymous_id": user["anonymous_id"],
            },
        )
        assert feedback_response.status_code == 200
        feedback = feedback_response.json()
        assert 1 <= len(feedback["replacement_candidates"]) <= 3

        selected_product_id = feedback["replacement_candidates"][0]["product"]["external_id"]
        selection_response = client.post(
            "/api/v1/recommendations/"
            f"{recommendation['recommendation_id']}/replacements/"
            f"{feedback['replacement_session_id']}/select",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "product_external_id": selected_product_id,
                "anonymous_id": user["anonymous_id"],
            },
        )

    assert selection_response.status_code == 200

    feedback_event = _find_event(
        {
            "event_type": AnalyticsEventType.FEEDBACK_SUBMITTED.value,
            "event_source": "server",
            "recommendation_id": recommendation["recommendation_id"],
        }
    )
    generated_event = _find_event(
        {
            "event_type": AnalyticsEventType.REPLACEMENT_GENERATED.value,
            "event_source": "server",
            "recommendation_id": recommendation["recommendation_id"],
        }
    )
    selected_event = _find_event(
        {
            "event_type": AnalyticsEventType.REPLACEMENT_SELECTED.value,
            "event_source": "server",
            "recommendation_id": recommendation["recommendation_id"],
            "product_external_id": selected_product_id,
        }
    )

    assert feedback_event is not None
    assert feedback_event["metadata"]["reason"] == "dislikes_brand"
    assert "comment" not in feedback_event["metadata"]
    assert generated_event is not None
    assert 1 <= generated_event["metadata"]["candidate_count"] <= 3
    assert selected_event is not None
    assert selected_event["metadata"]["replacement_session_id"] == feedback[
        "replacement_session_id"
    ]


def test_profile_update_is_recorded_without_personal_profile_values() -> None:
    with TestClient(app) as client:
        token, user = _register(client)
        response = client.patch(
            "/api/v1/users/me/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "skin_type": "dry",
                "concerns": ["dryness"],
                "budget": "balanced",
            },
        )

    assert response.status_code == 200
    event = _find_event(
        {
            "event_type": AnalyticsEventType.PROFILE_SAVED.value,
            "event_source": "server",
            "user_id": user["user_id"],
            "metadata.source": "profile_update",
        }
    )

    assert event is not None
    assert event["metadata"]["skin_type"] == "dry"
    assert "full_name" not in event["metadata"]
    assert "email" not in event["metadata"]


def test_llm_fallback_is_recorded_by_backend() -> None:
    with TestClient(app) as client:
        token, user = _register(client)
        response = client.post(
            "/api/v1/llm/explanations/preview",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "skin_type": "combination",
                "concerns": ["acne"],
                "matched_concerns": ["acne"],
                "name": "Dataset Product",
                "brand": "Dataset Brand",
                "step": "serum",
                "ingredients": ["niacinamide"],
                "concern_match": 1,
                "use_llm": False,
            },
        )

    assert response.status_code == 200
    assert response.json()["used_llm"] is False

    event = _find_event(
        {
            "event_type": AnalyticsEventType.LLM_EXPLANATION_FALLBACK.value,
            "event_source": "server",
            "user_id": user["user_id"],
            "metadata.step": "serum",
        }
    )

    assert event is not None
    assert event["metadata"]["fallback_reason"] == "llm_not_requested"
    assert "user_prompt" not in event["metadata"]
    assert "system_prompt" not in event["metadata"]


def test_questionnaire_completed_cannot_be_spoofed_via_public_endpoint() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/analytics/events",
            json={
                "event_type": "questionnaire_completed",
                "anonymous_id": "spoof-attempt",
                "metadata": {},
            },
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_analytics_failure_does_not_break_business_flow() -> None:
    class FailingRepository:
        async def save_event(self, **kwargs):
            raise RuntimeError("analytics unavailable")

    tracker = EventTrackingService(FailingRepository())

    result = await tracker.record(
        AnalyticsEventType.PROFILE_SAVED,
        user_id="test-user",
        metadata={"source": "unit-test"},
    )

    assert result is None
