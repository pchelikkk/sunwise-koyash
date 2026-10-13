from app.algorithms.normalizer import normalized_request
from app.schemas.recommendation import RecommendationRequest


def _request(concerns: list[str]) -> RecommendationRequest:
    return RecommendationRequest(
        age=24,
        skin_type="combination",
        concerns=concerns,
        budget="balanced",
        excluded_ingredients=[],
        custom_restrictions=[],
        experience="guided",
        values=[],
        anonymous_id="normalizer-test",
    )


def test_reactivity_stays_aligned_with_dataset_concern() -> None:
    normalized = normalized_request(_request(["reactivity", "unknown"]))

    assert normalized.concerns == ["reactivity"]


def test_sensitivity_alias_maps_to_reactivity() -> None:
    normalized = normalized_request(_request(["sensitivity", "чувствительность", "реактивность"]))

    assert normalized.concerns == ["reactivity"]
