from types import SimpleNamespace
from uuid import uuid4

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient
from pydantic import ValidationError
from pymongo import DESCENDING, MongoClient

from app.core.config import get_settings
from app.main import app
from app.schemas.analytics import AnalyticsEventCreate
from app.schemas.llm import LLMExplanationPreviewRequest
from app.services.event_tracking_service import _sanitize_metadata
from app.services.llm_explanation_service import LLMExplanationService


def _database():
    settings = get_settings()
    client = MongoClient(
        settings.mongo_uri,
        uuidRepresentation="standard",
        serverSelectionTimeoutMS=5000,
    )
    return client, client[settings.mongo_db_name]


def _register(client: TestClient) -> tuple[str, dict]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"hardening-{uuid4().hex}@example.com",
            "password": "StrongPassword123!",
            "full_name": "Hardening Test User",
            "anonymous_id": f"trusted-{uuid4().hex}",
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


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "access_token",
        "password_hash",
        "user_email",
        "providerApiKey",
        "system-prompt",
        "session_cookie",
    ],
)
def test_public_metadata_rejects_sensitive_key_variants(forbidden_key: str) -> None:
    with pytest.raises(ValidationError):
        AnalyticsEventCreate(
            event_type="product_viewed",
            metadata={"nested": {forbidden_key: "secret"}},
        )


def test_server_metadata_sanitizer_removes_sensitive_key_variants() -> None:
    sanitized = _sanitize_metadata(
        {
            "safe": "value",
            "access_token": "secret-token",
            "nested": {
                "password_hash": "secret-hash",
                "user_email": "private@example.com",
                "candidate_count": 2,
            },
        }
    )

    assert sanitized == {
        "safe": "value",
        "nested": {"candidate_count": 2},
    }


def test_server_metadata_sanitizer_preserves_non_sensitive_aggregate_flags() -> None:
    sanitized = _sanitize_metadata(
        {
            "name_provided": True,
            "pre_registration_session_linked": True,
        }
    )

    assert sanitized == {
        "name_provided": True,
        "pre_registration_session_linked": True,
    }


def test_authenticated_recommendation_uses_server_identity_not_payload_identity() -> None:
    forged_anonymous_id = f"forged-{uuid4().hex}"

    with TestClient(app) as client:
        token, user = _register(client)
        response = client.post(
            "/api/v1/recommendations",
            headers={"Authorization": f"Bearer {token}"},
            json=_recommendation_payload(forged_anonymous_id),
        )

    assert response.status_code == 200
    recommendation_id = response.json()["recommendation_id"]

    mongo_client, database = _database()
    try:
        recommendation = database["recommendation_sessions"].find_one(
            {"_id": ObjectId(recommendation_id)}
        )
        event = database["analytics_events"].find_one(
            {
                "recommendation_id": recommendation_id,
                "event_type": "questionnaire_completed",
            },
            sort=[("created_at", DESCENDING)],
        )
    finally:
        mongo_client.close()

    assert recommendation is not None
    assert recommendation["anonymous_id"] == user["anonymous_id"]
    assert recommendation["request"]["anonymous_id"] == user["anonymous_id"]
    assert recommendation["anonymous_id"] != forged_anonymous_id
    assert event is not None
    assert event["anonymous_id"] == user["anonymous_id"]


def test_feedback_uses_recommendation_identity_not_feedback_payload_identity() -> None:
    forged_feedback_identity = f"feedback-forged-{uuid4().hex}"

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
                "anonymous_id": forged_feedback_identity,
            },
        )

    assert feedback_response.status_code == 200

    mongo_client, database = _database()
    try:
        feedback = database["feedback_events"].find_one(
            {"feedback_id": feedback_response.json()["feedback_id"]}
        )
        if feedback is None:
            feedback = database["feedback_events"].find_one(
                {"recommendation_id": recommendation["recommendation_id"]},
                sort=[("created_at", DESCENDING)],
            )
        event = database["analytics_events"].find_one(
            {
                "recommendation_id": recommendation["recommendation_id"],
                "event_type": "feedback_submitted",
            },
            sort=[("created_at", DESCENDING)],
        )
    finally:
        mongo_client.close()

    assert feedback is not None
    assert feedback["anonymous_id"] == user["anonymous_id"]
    assert feedback["anonymous_id"] != forged_feedback_identity
    assert event is not None
    assert event["anonymous_id"] == user["anonymous_id"]


@pytest.mark.asyncio
async def test_empty_llm_provider_response_uses_deterministic_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeCompletions:
        async def create(self, **kwargs):
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content="   "),
                    )
                ]
            )

    class FakeAsyncOpenAI:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr(
        "app.services.llm_explanation_service.AsyncOpenAI",
        FakeAsyncOpenAI,
    )

    service = LLMExplanationService()
    monkeypatch.setattr(service.settings, "llm_enabled", True)
    monkeypatch.setattr(service.settings, "vsellm_api_key", "test-key")

    response = await service.preview(
        LLMExplanationPreviewRequest(
            skin_type="combination",
            concerns=["acne"],
            matched_concerns=["acne"],
            name="Dataset Product",
            brand="Dataset Brand",
            step="serum",
            ingredients=["niacinamide"],
            concern_match=1,
            use_llm=True,
        )
    )

    assert response.used_llm is False
    assert response.provider == "deterministic-fallback"
    assert response.explanation
