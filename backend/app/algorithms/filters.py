from collections import Counter
from dataclasses import dataclass
from typing import Any

from app.algorithms.normalizer import normalize_restriction, normalize_text
from app.schemas.recommendation import RecommendationRequest

FRAGRANCE_RESTRICTIONS = {
    "fragrance",
    "fragrances",
    "parfum",
    "perfume",
    "отдушка",
    "отдушки",
    "ароматизатор",
    "ароматизаторы",
}

FRAGRANCE_POSITIVE_FLAGS = {
    "contains_fragrance",
    "fragrance",
    "parfum",
    "perfume",
}

FRAGRANCE_SAFE_FLAGS = {
    "fragrance_free",
    "без отдушек",
    "без отдушки",
}


ALCOHOL_RESTRICTIONS = {
    "alcohol",
    "ethanol",
    "ethyl alcohol",
    "alcohol denat",
    "denatured alcohol",
    "sd alcohol",
    "спирт",
    "спирты",
    "этанол",
    "денатурированный спирт",
}

ALCOHOL_POSITIVE_FLAGS = {
    "contains_alcohol",
    "drying_alcohol",
    "alcohol",
    "alcohol_denat",
}

ALCOHOL_SAFE_FLAGS = {
    "alcohol_free",
    "без спирта",
}


ESSENTIAL_OIL_RESTRICTIONS = {
    "essential_oils",
    "essential oil",
    "essential oils",
    "эфирное масло",
    "эфирные масла",
}

ESSENTIAL_OIL_POSITIVE_FLAGS = {
    "contains_essential_oils",
    "essential_oils",
}

SENSITIVE_IRRITANT_FLAGS = {
    "contains_alcohol",
    "contains_essential_oils",
    "contains_fragrance",
}

BUDGET_PRICE_CAPS_RUB = {
    "minimum": 1200,
    "balanced": 2200,
}


@dataclass(frozen=True)
class FilterResult:
    allowed_products: list[dict]
    filter_reasons: dict[str, int]
    restriction_match_counts: dict[str, int]


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, (tuple, set)):
        return list(value)

    return [value]


def _lowered_strings(value: Any) -> list[str]:
    result: list[str] = []

    for item in _as_list(value):
        text = str(item).strip().lower()
        if text:
            result.append(text)

    return result


def _normalized_variants(value: str) -> set[str]:
    raw = str(value or "").strip()

    if not raw:
        return set()

    lowered = raw.lower()

    return {
        lowered,
        normalize_text(raw),
        normalize_restriction(raw),
    } - {""}


def _ingredients(product: dict) -> set[str]:
    result: set[str] = set()

    for item in _lowered_strings(product.get("ingredients")):
        result.update(_normalized_variants(item))

    return result


def _flags(product: dict) -> set[str]:
    result: set[str] = set()

    for field in (
        "ingredient_flags",
        "risk_flags",
        "excluded_ingredient_flags",
        "avoid_if",
    ):
        for item in _lowered_strings(product.get(field)):
            result.update(_normalized_variants(item))

    return result


def _has_exact_or_phrase_match(values: set[str], markers: set[str]) -> bool:
    for value in values:
        if value in markers:
            return True

    return False


def _matches_fragrance(product: dict) -> bool:
    ingredients = _ingredients(product)
    flags = _flags(product)

    # Safe flags must not be treated as forbidden.
    # Example: "fragrance_free" contains the word "fragrance",
    # but it means the opposite.
    if flags.intersection(FRAGRANCE_SAFE_FLAGS):
        positive_flags = flags.intersection(FRAGRANCE_POSITIVE_FLAGS)
        return bool(positive_flags)

    if flags.intersection(FRAGRANCE_POSITIVE_FLAGS):
        return True

    if ingredients.intersection(FRAGRANCE_RESTRICTIONS):
        return True

    return False


def _matches_alcohol(product: dict) -> bool:
    ingredients = _ingredients(product)
    flags = _flags(product)

    if flags.intersection(ALCOHOL_SAFE_FLAGS):
        positive_flags = flags.intersection(ALCOHOL_POSITIVE_FLAGS)
        return bool(positive_flags)

    if flags.intersection(ALCOHOL_POSITIVE_FLAGS):
        return True

    if ingredients.intersection(ALCOHOL_RESTRICTIONS):
        return True

    return False


def _matches_essential_oils(product: dict) -> bool:
    ingredients = _ingredients(product)
    flags = _flags(product)

    if flags.intersection(ESSENTIAL_OIL_POSITIVE_FLAGS):
        return True

    if ingredients.intersection(ESSENTIAL_OIL_RESTRICTIONS):
        return True

    return False


def product_matches_restriction(product: dict, restriction: str) -> bool:
    variants = _normalized_variants(restriction)

    if not variants:
        return False

    if variants.intersection({"none", "no", "нет", "unknown", "не знаю"}):
        return False

    if variants.intersection(FRAGRANCE_RESTRICTIONS):
        return _matches_fragrance(product)

    if variants.intersection(ALCOHOL_RESTRICTIONS):
        return _matches_alcohol(product)

    if variants.intersection(ESSENTIAL_OIL_RESTRICTIONS):
        return _matches_essential_oils(product)

    ingredients = _ingredients(product)
    flags = _flags(product)

    return bool(ingredients.intersection(variants) or flags.intersection(variants))


def product_matches_any_restriction(product: dict, restrictions: list[str] | set[str]) -> bool:
    return any(product_matches_restriction(product, restriction) for restriction in restrictions)


def _request_restrictions(request: RecommendationRequest) -> list[str]:
    return list(
        dict.fromkeys(
            [
                *request.excluded_ingredients,
                *request.custom_restrictions,
            ]
        )
    )


def product_filter_reason(product: dict, request: RecommendationRequest) -> str | None:
    if not product.get("is_active", True):
        return "inactive"

    restrictions = _request_restrictions(request)

    if restrictions and product_matches_any_restriction(product, restrictions):
        return "excluded_ingredient"

    risk_flags = set(_lowered_strings(product.get("risk_flags")))

    sensitive_profile = (
        normalize_text(request.skin_type) == "sensitive"
        or request.sensitivity_level == "high"
    )
    if sensitive_profile and risk_flags.intersection(SENSITIVE_IRRITANT_FLAGS):
        return "sensitive_risk"

    if (
        normalize_text(request.experience) in {"beginner", "minimal"}
        and "active_formula" in risk_flags
    ):
        return "beginner_safety"

    normalized_budget = normalize_text(request.budget)
    price_cap = BUDGET_PRICE_CAPS_RUB.get(normalized_budget)
    if price_cap is not None and int(product.get("price_rub", 0) or 0) > price_cap:
        return "budget_hard_cap"

    return None


def apply_hard_filters(
    products: list[dict],
    request: RecommendationRequest,
) -> FilterResult:
    allowed: list[dict] = []
    reasons: Counter[str] = Counter()
    restrictions = _request_restrictions(request)
    restriction_matches: Counter[str] = Counter()

    for product in products:
        for restriction in restrictions:
            if product_matches_restriction(product, restriction):
                restriction_matches[restriction] += 1

        reason = product_filter_reason(product, request)

        if reason is not None:
            reasons[reason] += 1
            continue

        allowed.append(product)

    return FilterResult(
        allowed_products=allowed,
        filter_reasons=dict(reasons),
        restriction_match_counts={
            restriction: restriction_matches[restriction]
            for restriction in restrictions
        },
    )
