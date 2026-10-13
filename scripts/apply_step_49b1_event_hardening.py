from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path.cwd()


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8-sig")


def write(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    ast.parse(content, filename=str(path))
    path.write_text(content, encoding="utf-8")


write(
    "backend/app/services/event_tracking_service.py",
    '''import json
import logging
import re
from enum import Enum
from typing import Any

from app.core.enums import AnalyticsEventSource, AnalyticsEventType
from app.repositories.analytics_repository import AnalyticsRepository

logger = logging.getLogger(__name__)

_FORBIDDEN_METADATA_KEY_PARTS = {
    "anonymous_id",
    "api_key",
    "authorization",
    "comment",
    "cookie",
    "credential",
    "email",
    "full_name",
    "password",
    "phone",
    "prompt",
    "secret",
    "token",
    "user_id",
}


def _normalized_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).casefold()).strip("_")


def _is_forbidden_metadata_key(value: Any) -> bool:
    normalized = _normalized_key(value)
    compact = normalized.replace("_", "")
    return any(
        part in normalized or part.replace("_", "") in compact
        for part in _FORBIDDEN_METADATA_KEY_PARTS
    )


def _sanitize_value(value: Any, depth: int = 0) -> Any:
    if depth > 4:
        return "[truncated]"

    if value is None or isinstance(value, bool | int | float):
        return value

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, str):
        return value[:240]

    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in list(value.items())[:30]:
            if _is_forbidden_metadata_key(key):
                continue
            result[str(key)[:80]] = _sanitize_value(item, depth + 1)
        return result

    if isinstance(value, list | tuple | set):
        return [_sanitize_value(item, depth + 1) for item in list(value)[:30]]

    return str(value)[:240]


def _sanitize_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    sanitized = _sanitize_value(metadata or {})
    result = sanitized if isinstance(sanitized, dict) else {}
    rendered = json.dumps(result, ensure_ascii=False, separators=(",", ":"))

    if len(rendered.encode("utf-8")) <= 4096:
        return result

    return {
        "metadata_truncated": True,
        "retained_keys": list(result)[:20],
    }


class EventTrackingService:
    """Best-effort server-owned analytics.

    Analytics failures are logged but never break registration, recommendations,
    feedback, replacements, profile updates, or LLM fallback behavior.
    """

    def __init__(self, analytics_repository: AnalyticsRepository) -> None:
        self.analytics_repository = analytics_repository

    async def record(
        self,
        event_type: AnalyticsEventType,
        *,
        anonymous_id: str | None = None,
        user_id: str | None = None,
        recommendation_id: str | None = None,
        product_external_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        try:
            return await self.analytics_repository.save_event(
                event_type=event_type.value,
                event_source=AnalyticsEventSource.SERVER.value,
                anonymous_id=anonymous_id,
                user_id=user_id,
                recommendation_id=recommendation_id,
                product_external_id=product_external_id,
                metadata=_sanitize_metadata(metadata),
            )
        except Exception:
            logger.exception(
                "Could not record server analytics event %s",
                event_type.value,
            )
            return None
''',
)


write(
    "backend/app/schemas/analytics.py",
    '''import json
import re
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import PublicAnalyticsEventType

_FORBIDDEN_METADATA_KEY_PARTS = {
    "anonymous_id",
    "api_key",
    "authorization",
    "comment",
    "cookie",
    "credential",
    "email",
    "full_name",
    "password",
    "phone",
    "prompt",
    "secret",
    "token",
    "user_id",
}


def _normalized_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).casefold()).strip("_")


def _is_forbidden_metadata_key(value: Any) -> bool:
    normalized = _normalized_key(value)
    compact = normalized.replace("_", "")
    return any(
        part in normalized or part.replace("_", "") in compact
        for part in _FORBIDDEN_METADATA_KEY_PARTS
    )


def _forbidden_metadata_keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        result: list[str] = []
        for key, item in value.items():
            if _is_forbidden_metadata_key(key):
                result.append(str(key))
            result.extend(_forbidden_metadata_keys(item))
        return result

    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(_forbidden_metadata_keys(item))
        return result

    return []


class AnalyticsEventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: PublicAnalyticsEventType
    anonymous_id: str | None = Field(default=None, max_length=120)
    recommendation_id: str | None = Field(default=None, max_length=120)
    product_external_id: str | None = Field(default=None, max_length=120)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        if len(value) > 30:
            raise ValueError("metadata contains too many top-level fields")

        forbidden = sorted(set(_forbidden_metadata_keys(value)))
        if forbidden:
            raise ValueError(
                "metadata contains forbidden fields: " + ", ".join(forbidden)
            )

        encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        if len(encoded.encode("utf-8")) > 4096:
            raise ValueError("metadata is larger than 4096 bytes")

        return value


class AnalyticsEventResponse(BaseModel):
    event_id: str
    status: str = "recorded"
    created_at: datetime


class AnalyticsSummaryResponse(BaseModel):
    total_events: int
    events_by_type: dict[str, int]
    top_products: list[dict[str, Any]]
    feedback_reasons: dict[str, int]
    recent_events: list[dict[str, Any]]
''',
)


recommendation_path = "backend/app/services/recommendation_service.py"
recommendation_text = read(recommendation_path)
old_identity = '''        normalized = normalized_request(request)\n        session_anonymous_id = normalized.anonymous_id or authenticated_anonymous_id\n\n        products = await self.product_repository.list_active_products()\n'''
new_identity = '''        normalized = normalized_request(request)\n        session_anonymous_id = (\n            authenticated_anonymous_id\n            if user_id is not None\n            else normalized.anonymous_id\n        )\n        request_payload = normalized.model_dump()\n        request_payload["anonymous_id"] = session_anonymous_id\n\n        products = await self.product_repository.list_active_products()\n'''
if old_identity in recommendation_text:
    recommendation_text = recommendation_text.replace(old_identity, new_identity, 1)
elif new_identity not in recommendation_text:
    raise RuntimeError("Could not patch trusted recommendation identity")

old_request_save = "            request=normalized.model_dump(),\n"
new_request_save = "            request=request_payload,\n"
if old_request_save in recommendation_text:
    recommendation_text = recommendation_text.replace(old_request_save, new_request_save, 1)
elif new_request_save not in recommendation_text:
    raise RuntimeError("Could not patch trusted recommendation request payload")
write(recommendation_path, recommendation_text)


feedback_path = "backend/app/services/feedback_service.py"
feedback_text = read(feedback_path)
old_feedback_block = '''        feedback = await self.feedback_repository.create(\n            recommendation_id=recommendation_id,\n            product_external_id=payload.product_external_id,\n            reason=payload.reason,\n            comment=payload.comment,\n            anonymous_id=payload.anonymous_id,\n        )\n'''
new_feedback_block = '''        recommendation_anonymous_id = recommendation.get("anonymous_id")\n\n        feedback = await self.feedback_repository.create(\n            recommendation_id=recommendation_id,\n            product_external_id=payload.product_external_id,\n            reason=payload.reason,\n            comment=payload.comment,\n            anonymous_id=recommendation_anonymous_id,\n        )\n'''
if old_feedback_block in feedback_text:
    feedback_text = feedback_text.replace(old_feedback_block, new_feedback_block, 1)
elif new_feedback_block not in feedback_text:
    raise RuntimeError("Could not patch trusted feedback identity")

old_feedback_identity = '''        user_id = recommendation.get("user_id")\n        anonymous_id = recommendation.get("anonymous_id") or payload.anonymous_id\n'''
new_feedback_identity = '''        user_id = recommendation.get("user_id")\n        anonymous_id = recommendation_anonymous_id\n'''
if old_feedback_identity in feedback_text:
    feedback_text = feedback_text.replace(old_feedback_identity, new_feedback_identity, 1)
elif new_feedback_identity not in feedback_text:
    raise RuntimeError("Could not patch feedback event identity")
write(feedback_path, feedback_text)


llm_path = "backend/app/services/llm_explanation_service.py"
llm_text = read(llm_path)
old_llm = '''            response = await client.chat.completions.create(\n                model=self.settings.vsellm_model,\n                messages=[\n                    {"role": "system", "content": system_prompt},\n                    {"role": "user", "content": user_prompt},\n                ],\n                temperature=0.2,\n                max_tokens=120,\n            )\n        except Exception as exc:\n'''
new_llm = '''            response = await client.chat.completions.create(\n                model=self.settings.vsellm_model,\n                messages=[\n                    {"role": "system", "content": system_prompt},\n                    {"role": "user", "content": user_prompt},\n                ],\n                temperature=0.2,\n                max_tokens=120,\n            )\n            explanation = (response.choices[0].message.content or "").strip()[:200]\n            if not explanation:\n                raise ValueError("empty_llm_response")\n        except Exception as exc:\n'''
if old_llm in llm_text:
    llm_text = llm_text.replace(old_llm, new_llm, 1)
elif new_llm not in llm_text:
    raise RuntimeError("Could not patch empty LLM response fallback")

old_explanation = '''        explanation = (response.choices[0].message.content or "").strip()[:200]\n\n        await self._record_result(\n'''
new_explanation = '''        await self._record_result(\n'''
if old_explanation in llm_text:
    llm_text = llm_text.replace(old_explanation, new_explanation, 1)
elif "raise ValueError(\"empty_llm_response\")" not in llm_text:
    raise RuntimeError("Could not remove duplicate LLM explanation extraction")
write(llm_path, llm_text)


write(
    "backend/tests/test_server_event_tracking_hardening.py",
    '''from types import SimpleNamespace
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
''',
)


doc_path = ROOT / "docs/analytics-event-contract.md"
doc_text = doc_path.read_text(encoding="utf-8-sig")
marker = "## Identity integrity"
if marker not in doc_text:
    doc_text = doc_text.rstrip() + '''

## Identity integrity

For authenticated recommendation requests, identity is taken from the authenticated
user record. A client-provided `anonymous_id` cannot replace that identity.
Feedback and replacement events inherit identity from the saved recommendation,
not from feedback request fields.

Sensitive metadata detection covers nested and compound key variants such as
`access_token`, `password_hash`, `user_email`, API keys, cookies, credentials,
and prompt fields.
'''
    doc_path.write_text(doc_text + "\n", encoding="utf-8")

print("STEP 4.9B.1 APPLIED")
print("- authenticated analytics identity cannot be spoofed by request payloads")
print("- compound and nested sensitive metadata keys are blocked")
print("- empty LLM provider responses use deterministic fallback")
print("- production dashboard work can proceed after tests pass")
