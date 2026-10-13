from app.algorithms.filters import product_filter_reason
from app.algorithms.normalizer import normalized_request
from app.algorithms.routine_builder import build_routine
from app.algorithms.scoring import ScoredProduct, score_product
from app.schemas.recommendation import RecommendationRequest, ScoreBreakdown


def _request(**overrides) -> RecommendationRequest:
    payload = {
        "age": 24,
        "skin_type": "combination",
        "concerns": ["acne", "dryness"],
        "primary_concern": "acne",
        "sensitivity_level": "medium",
        "budget": "balanced",
        "excluded_ingredients": [],
        "custom_restrictions": [],
        "experience": "beginner",
        "routine_preference": "balanced",
        "texture_preference": "no_preference",
        "values": ["soft_formula"],
    }
    payload.update(overrides)
    return RecommendationRequest(**payload)


def _product(
    external_id: str,
    step: str,
    **overrides,
) -> dict:
    product = {
        "external_id": external_id,
        "name": external_id,
        "routine_step": step,
        "concerns": ["acne"],
        "skin_types": ["all"],
        "budget_segment": "balanced",
        "price_rub": 900,
        "risk_flags": [],
        "ingredient_flags": [],
        "values": [],
        "texture": "Крем",
        "is_active": True,
    }
    product.update(overrides)
    return product


def _scored(external_id: str, step: str) -> ScoredProduct:
    return ScoredProduct(
        product=_product(external_id, step),
        score=ScoreBreakdown(total=100),
    )


def _steps(routine: dict, daypart: str) -> list[str]:
    return [item.product["routine_step"] for item in routine[daypart]]


def test_primary_concern_is_normalized_and_included_in_concerns() -> None:
    request = _request(
        concerns=["dryness"],
        primary_concern="sensitivity",
        texture_preference="lightweight",
        routine_preference="complete",
    )

    normalized = normalized_request(request)

    assert normalized.primary_concern == "reactivity"
    assert normalized.concerns == ["reactivity", "dryness"]
    assert normalized.texture_preference == "lightweight"
    assert normalized.routine_preference == "complete"


def test_legacy_simple_routine_maps_to_minimal_preference() -> None:
    normalized = normalized_request(
        _request(values=["simple_routine"], routine_preference="balanced")
    )

    assert normalized.values == ["minimal_steps"]
    assert normalized.routine_preference == "minimal"


def test_primary_concern_has_explicit_score_component() -> None:
    product = _product("serum", "serum")
    primary_match = score_product(product, _request(primary_concern="acne"))
    secondary_match = score_product(product, _request(primary_concern="dryness"))

    assert primary_match.primary_concern_score == 7
    assert secondary_match.primary_concern_score == 0
    assert primary_match.total == secondary_match.total + 7


def test_all_skin_type_and_texture_preferences_are_scored() -> None:
    product = _product("gel", "serum", texture="Гель")
    score = score_product(
        product,
        _request(texture_preference="lightweight"),
    )

    assert score.skin_type_score == 10
    assert score.texture_score == 6


def test_high_sensitivity_filters_known_irritants_not_context_labels() -> None:
    request = _request(sensitivity_level="high")
    fragrance = _product(
        "fragrance",
        "moisturizer",
        risk_flags=["contains_fragrance"],
    )
    contextual = _product(
        "contextual",
        "moisturizer",
        risk_flags=["sensitive_attention"],
    )

    assert product_filter_reason(fragrance, request) == "sensitive_risk"
    assert product_filter_reason(contextual, request) is None


def test_each_bounded_budget_is_a_hard_per_product_limit() -> None:
    minimum_request = _request(budget="minimum")
    balanced_request = _request(budget="balanced")

    assert product_filter_reason(
        _product("minimum-too-expensive", "serum", price_rub=1201),
        minimum_request,
    ) == "budget_hard_cap"
    assert product_filter_reason(
        _product("balanced-too-expensive", "serum", price_rub=2201),
        balanced_request,
    ) == "budget_hard_cap"
    assert product_filter_reason(
        _product("balanced-at-cap", "serum", price_rub=2200),
        balanced_request,
    ) is None


def test_routine_preference_changes_schedule_without_breaking_base_steps() -> None:
    products = [
        _scored("cleanser", "cleanser"),
        _scored("toner", "toner"),
        _scored("serum", "serum"),
        _scored("treatment", "treatment"),
        _scored("moisturizer", "moisturizer"),
        _scored("spf", "spf"),
    ]

    minimal = build_routine(products, "beginner", "minimal")
    balanced = build_routine(products, "beginner", "balanced")
    complete = build_routine(products, "basic", "complete")

    assert _steps(minimal, "morning") == ["cleanser", "moisturizer", "spf"]
    assert _steps(minimal, "evening") == ["cleanser", "moisturizer"]
    assert _steps(balanced, "evening") == [
        "cleanser",
        "toner",
        "serum",
        "moisturizer",
    ]
    assert _steps(complete, "morning") == [
        "cleanser",
        "toner",
        "moisturizer",
        "spf",
    ]
    assert _steps(complete, "evening") == [
        "cleanser",
        "toner",
        "serum",
        "treatment",
        "moisturizer",
    ]
