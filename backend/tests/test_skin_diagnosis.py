import pytest
from fastapi.testclient import TestClient

from app.algorithms.skin_diagnosis import diagnose_skin_type
from app.main import app
from app.schemas.skin_diagnosis import SkinDiagnosticAnswers


@pytest.mark.parametrize(
    ("answers", "expected"),
    [
        (
            {
                "after_cleansing": "comfortable",
                "midday_shine": "all_over",
                "pore_visibility": "widely_visible",
                "flaking": "never",
            },
            "oily",
        ),
        (
            {
                "after_cleansing": "very_tight",
                "midday_shine": "none",
                "pore_visibility": "barely_visible",
                "flaking": "often",
            },
            "dry",
        ),
        (
            {
                "after_cleansing": "slightly_tight",
                "midday_shine": "t_zone",
                "pore_visibility": "t_zone_visible",
                "flaking": "sometimes",
            },
            "combination",
        ),
        (
            {
                "after_cleansing": "comfortable",
                "midday_shine": "none",
                "pore_visibility": "barely_visible",
                "flaking": "never",
            },
            "normal",
        ),
    ],
)
def test_guided_diagnosis_is_deterministic(answers: dict, expected: str) -> None:
    first = diagnose_skin_type(SkinDiagnosticAnswers(**answers))
    second = diagnose_skin_type(SkinDiagnosticAnswers(**answers))

    assert first == second
    assert first.resolved_skin_type == expected
    assert len(first.signals) == 4
    assert 0 <= first.confidence_percent <= 100


def test_skin_diagnosis_endpoint_rejects_incomplete_answers() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/skin-diagnosis",
            json={"after_cleansing": "comfortable"},
        )

    assert response.status_code == 422


def test_unknown_skin_type_requires_guided_answers() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/recommendations",
            json={
                "skin_type": "unknown",
                "concerns": ["dryness"],
                "budget": "balanced",
            },
        )

    assert response.status_code == 422


def test_recommendation_resolves_unknown_skin_type() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/recommendations",
            json={
                "skin_type": "unknown",
                "skin_diagnostic_answers": {
                    "after_cleansing": "slightly_tight",
                    "midday_shine": "t_zone",
                    "pore_visibility": "t_zone_visible",
                    "flaking": "sometimes",
                },
                "concerns": ["acne", "sebum"],
                "primary_concern": "acne",
                "budget": "balanced",
                "experience": "beginner",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["skin_profile"]["method"] == "guided_diagnostic"
    assert payload["skin_profile"]["submitted_skin_type"] == "unknown"
    assert payload["skin_profile"]["resolved_skin_type"] == "combination"
    assert payload["routine"]["morning"]
