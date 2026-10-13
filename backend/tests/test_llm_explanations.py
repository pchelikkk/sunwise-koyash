import ast
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


def _safe_explanation_from_user_prompt(user_prompt: str) -> str:
    values = {
        line.split(":", 1)[0]: line.split(":", 1)[1].strip()
        for line in user_prompt.splitlines()
        if ":" in line
    }
    product = values["Продукт"].rsplit(" (", 1)[0]
    ingredients = ast.literal_eval(values["Состав"])
    matched = ast.literal_eval(
        values[
            "Засчитанные движком боли для этого продукта (matched_concerns)"
        ]
    )
    ingredient = ingredients[0]
    if matched:
        return (
            f"Внутри {ingredient}; в уходе его связывают с запросом "
            f"«{matched[0]}»."
        )
    return f"Для шага ухода выбрали {product}. Внутри {ingredient}."


def test_llm_demo_payloads_are_available() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/llm/explanations/demo-payloads")

    assert response.status_code == 200
    payload = response.json()

    assert len(payload["payloads"]) == 3
    assert payload["payloads"][0]["concern_match"] == 0


def test_llm_preview_fallback_does_not_call_external_api() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/llm/explanations/preview",
            json={
                "skin_type": "combination",
                "concerns": ["acne", "sebum"],
                "matched_concerns": [],
                "name": "Gentle Balance Cleanser",
                "brand": "Koyash Sample",
                "step": "cleanser",
                "ingredients": ["amino acid surfactants", "glycerin", "panthenol"],
                "concern_match": 0,
                "use_llm": False,
            },
        )

    assert response.status_code == 200
    payload = response.json()

    assert payload["used_llm"] is False
    assert payload["explanation"]
    assert "system_prompt" in payload
    assert "user_prompt" in payload
    assert "Тип кожи пользователя" in payload["user_prompt"]
    assert "matched_concerns): []" in payload["user_prompt"]
    assert "единственный источник истины" in payload["system_prompt"]


def test_recommendation_flow_uses_llm_only_for_explanations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeCompletions:
        async def create(self, **kwargs):
            explanation = _safe_explanation_from_user_prompt(
                kwargs["messages"][1]["content"]
            )
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content=explanation
                        )
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
    settings = get_settings()
    monkeypatch.setattr(settings, "llm_enabled", True)
    monkeypatch.setattr(settings, "llm_provider", "vsellm")
    monkeypatch.setattr(settings, "vsellm_api_key", "test-key")

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/recommendations",
            json={
                "skin_type": "combination",
                "concerns": ["acne"],
                "budget": "balanced",
                "anonymous_id": "llm-flow-test",
            },
        )

    assert response.status_code == 200
    items = [
        *response.json()["routine"]["morning"],
        *response.json()["routine"]["evening"],
    ]
    assert items
    assert all(item["explanation_source"] == "llm" for item in items)
    assert all(item["explanation_model"] for item in items)
    assert all(item["score_breakdown"]["total"] == item["score"] for item in items)


def test_recommendation_flow_rejects_unsafe_llm_claims(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class UnsafeCompletions:
        async def create(self, **kwargs):
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content="Гарантированно вылечит акне и устранит все проблемы.",
                        )
                    )
                ]
            )

    class FakeAsyncOpenAI:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(completions=UnsafeCompletions())

    monkeypatch.setattr(
        "app.services.llm_explanation_service.AsyncOpenAI",
        FakeAsyncOpenAI,
    )
    settings = get_settings()
    monkeypatch.setattr(settings, "llm_enabled", True)
    monkeypatch.setattr(settings, "llm_provider", "vsellm")
    monkeypatch.setattr(settings, "vsellm_api_key", "test-key")

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/recommendations",
            json={
                "skin_type": "combination",
                "concerns": ["acne"],
                "budget": "balanced",
                "anonymous_id": "llm-unsafe-test",
            },
        )

    assert response.status_code == 200
    items = [
        *response.json()["routine"]["morning"],
        *response.json()["routine"]["evening"],
    ]
    assert items
    assert all(item["explanation_source"] == "deterministic" for item in items)
    assert all("вылечит" not in item["why_here"].lower() for item in items)


def test_openai_provider_uses_responses_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}

    class FakeResponses:
        async def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                output_text=(
                    "Внутри glycerin; в уходе его связывают с запросом «dryness»."
                )
            )

    class FakeAsyncOpenAI:
        def __init__(self, **kwargs):
            captured["client"] = kwargs
            self.responses = FakeResponses()

    monkeypatch.setattr(
        "app.services.llm_explanation_service.AsyncOpenAI",
        FakeAsyncOpenAI,
    )
    settings = get_settings()
    monkeypatch.setattr(settings, "llm_enabled", True)
    monkeypatch.setattr(settings, "llm_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "test-openai-key")
    monkeypatch.setattr(settings, "openai_model", "gpt-test")

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/llm/explanations/preview",
            json={
                "skin_type": "combination",
                "concerns": ["dryness"],
                "matched_concerns": ["dryness"],
                "name": "Barrier Serum",
                "brand": "Koyash Sample",
                "step": "serum",
                "ingredients": ["glycerin", "panthenol"],
                "concern_match": 1,
                "use_llm": True,
            },
        )

    assert response.status_code == 200
    assert response.json()["used_llm"] is True
    assert response.json()["provider"] == "openai"
    assert response.json()["model"] == "gpt-test"
    assert captured["model"] == "gpt-test"
    assert captured["max_output_tokens"] == 120
    assert "instructions" in captured
    assert "input" in captured
    assert captured["client"]["api_key"] == "test-openai-key"


def test_llm_preview_rejects_inconsistent_matched_concern_count() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/llm/explanations/preview",
            json={
                "skin_type": "combination",
                "concerns": ["dryness", "acne"],
                "matched_concerns": ["dryness"],
                "name": "Barrier Serum",
                "brand": "Koyash Sample",
                "step": "serum",
                "ingredients": ["glycerin"],
                "concern_match": 2,
                "use_llm": False,
            },
        )

    assert response.status_code == 422


def test_customer_prompt_keeps_user_and_matched_concerns_separate() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/llm/explanations/preview",
            json={
                "skin_type": "combination",
                "concerns": ["dryness", "acne"],
                "matched_concerns": ["dryness"],
                "name": "Barrier Serum",
                "brand": "Koyash Sample",
                "step": "serum",
                "ingredients": ["glycerin"],
                "concern_match": 1,
                "use_llm": False,
            },
        )

    assert response.status_code == 200
    prompt = response.json()["user_prompt"]
    assert "(concerns): ['dryness', 'acne']" in prompt
    assert "(matched_concerns): ['dryness']" in prompt
