from pathlib import Path

ROOT = Path(r"C:\Projects\sunwise-koyash")


def write_file(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")


write_file("backend/app/algorithms/filters.py", r'''
from collections import Counter
from dataclasses import dataclass
from typing import Any

from app.algorithms.normalizer import normalize_restriction, normalize_text
from app.schemas.recommendation import RecommendationRequest


FRAGRANCE_ALIASES = {
    "fragrance",
    "fragrances",
    "parfum",
    "perfume",
    "aroma",
    "отдушка",
    "отдушки",
    "ароматизатор",
    "ароматизаторы",
}

ALCOHOL_ALIASES = {
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

ESSENTIAL_OIL_ALIASES = {
    "essential_oils",
    "essential oil",
    "essential oils",
    "эфирное масло",
    "эфирные масла",
}


@dataclass(frozen=True)
class FilterResult:
    allowed_products: list[dict]
    filter_reasons: dict[str, int]


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, tuple | set):
        return list(value)

    return [value]


def _lower_items(value: Any) -> set[str]:
    return {str(item).strip().lower() for item in _as_list(value) if str(item).strip()}


def _normalized_items(value: Any) -> set[str]:
    result: set[str] = set()

    for item in _as_list(value):
        text = str(item).strip()
        if not text:
            continue

        result.add(text.lower())
        result.add(normalize_text(text))
        result.add(normalize_restriction(text))

    return {item for item in result if item}


def _product_ingredient_tokens(product: dict) -> set[str]:
    tokens: set[str] = set()

    for field in (
        "ingredients",
        "ingredient_flags",
        "risk_flags",
        "excluded_ingredient_flags",
        "avoid_if",
    ):
        tokens.update(_normalized_items(product.get(field)))

    return tokens


def _restriction_variants(restriction: str) -> set[str]:
    text = str(restriction).strip()

    if not text:
        return set()

    return {
        text.lower(),
        normalize_text(text),
        normalize_restriction(text),
    }


def _is_none_restriction(variants: set[str]) -> bool:
    return bool(variants.intersection({"", "none", "no", "нет", "unknown", "не знаю"}))


def _matches_fragrance(product: dict) -> bool:
    ingredients = _normalized_items(product.get("ingredients"))
    flags = _normalized_items(product.get("risk_flags")) | _normalized_items(
        product.get("ingredient_flags")
    )

    if ingredients.intersection(FRAGRANCE_ALIASES):
        return True

    if flags.intersection({"contains_fragrance", "fragrance"}):
        return True

    joined = " ".join(sorted(ingredients | flags))
    return "fragrance" in joined or "parfum" in joined


def _matches_alcohol(product: dict) -> bool:
    ingredients = _normalized_items(product.get("ingredients"))
    flags = _normalized_items(product.get("risk_flags")) | _normalized_items(
        product.get("ingredient_flags")
    )

    if ingredients.intersection(ALCOHOL_ALIASES):
        return True

    if flags.intersection({"contains_alcohol", "drying_alcohol", "alcohol"}):
        return True

    joined = " ".join(sorted(ingredients | flags))
    return "alcohol denat" in joined or "denatured alcohol" in joined


def _matches_essential_oils(product: dict) -> bool:
    ingredients = _normalized_items(product.get("ingredients"))
    flags = _normalized_items(product.get("risk_flags")) | _normalized_items(
        product.get("ingredient_flags")
    )

    if ingredients.intersection(ESSENTIAL_OIL_ALIASES):
        return True

    if flags.intersection({"contains_essential_oils", "essential_oils"}):
        return True

    joined = " ".join(sorted(ingredients | flags))
    return "essential oil" in joined or "essential oils" in joined


def product_matches_restriction(product: dict, restriction: str) -> bool:
    variants = _restriction_variants(restriction)

    if not variants or _is_none_restriction(variants):
        return False

    if variants.intersection(FRAGRANCE_ALIASES):
        return _matches_fragrance(product)

    if variants.intersection(ALCOHOL_ALIASES):
        return _matches_alcohol(product)

    if variants.intersection(ESSENTIAL_OIL_ALIASES):
        return _matches_essential_oils(product)

    product_tokens = _product_ingredient_tokens(product)
    return bool(product_tokens.intersection(variants))


def product_matches_any_restriction(product: dict, restrictions: list[str] | set[str]) -> bool:
    return any(product_matches_restriction(product, restriction) for restriction in restrictions)


def product_filter_reason(product: dict, request: RecommendationRequest) -> str | None:
    if not product.get("is_active", True):
        return "inactive"

    restrictions = set(request.excluded_ingredients + request.custom_restrictions)

    if product_matches_any_restriction(product, restrictions):
        return "excluded_ingredient"

    risk_flags = _lower_items(product.get("risk_flags"))

    if normalize_text(request.skin_type) == "sensitive" and risk_flags:
        return "sensitive_risk"

    if normalize_text(request.experience) in {"beginner", "minimal"} and "active_formula" in risk_flags:
        return "beginner_safety"

    if normalize_text(request.budget) == "minimum" and product.get("price_rub", 0) > 1200:
        return "budget_hard_cap"

    return None


def apply_hard_filters(
    products: list[dict],
    request: RecommendationRequest,
) -> FilterResult:
    allowed: list[dict] = []
    reasons: Counter[str] = Counter()

    for product in products:
        reason = product_filter_reason(product, request)

        if reason is not None:
            reasons[reason] += 1
            continue

        allowed.append(product)

    return FilterResult(allowed_products=allowed, filter_reasons=dict(reasons))
''')


write_file("backend/app/algorithms/replacement_strategy.py", r'''
from typing import Any

from app.algorithms.filters import product_filter_reason
from app.schemas.recommendation import RecommendationRequest


REASON_LABELS = {
    "too_expensive": "дешевле",
    "dislikes_brand": "другой бренд",
    "composition_concern": "меньше спорных отметок по составу",
    "texture_not_suitable": "другая текстура",
    "too_many_steps": "проще для рутины",
    "other": "альтернатива по тем же правилам подбора",
}


RISK_KEYS = (
    "risk_flags",
    "ingredient_flags",
    "excluded_ingredient_flags",
    "avoid_if",
)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, tuple | set):
        return list(value)

    return [value]


def _string_list(value: Any) -> list[str]:
    return [str(item).strip() for item in _as_list(value) if str(item).strip()]


def _lower_set(value: Any) -> set[str]:
    return {str(item).strip().lower() for item in _as_list(value) if str(item).strip()}


def _product_id(product: dict[str, Any]) -> str:
    return str(product.get("external_id") or product.get("product_id") or product.get("_id") or "")


def _price(product: dict[str, Any]) -> int:
    try:
        return int(product.get("price_rub") or 0)
    except (TypeError, ValueError):
        return 0


def _risk_flags(product: dict[str, Any]) -> set[str]:
    flags: set[str] = set()

    for key in RISK_KEYS:
        flags.update(_lower_set(product.get(key)))

    return flags


def _texture(product: dict[str, Any]) -> str:
    return str(product.get("texture") or product.get("format") or product.get("product_format") or "").lower()


def _brand(product: dict[str, Any]) -> str:
    return str(product.get("brand") or "").lower()


def _routine_step(product: dict[str, Any]) -> str:
    return str(product.get("routine_step") or product.get("step") or "").lower()


def _concerns(product: dict[str, Any]) -> set[str]:
    return _lower_set(product.get("concerns")) | _lower_set(product.get("matched_concerns"))


def _skin_types(product: dict[str, Any]) -> set[str]:
    return _lower_set(product.get("skin_types")) | _lower_set(product.get("suitable_skin_types"))


def _values(product: dict[str, Any]) -> set[str]:
    return _lower_set(product.get("values")) | _lower_set(product.get("tags"))


def _recommendation_context(recommendation: dict[str, Any]) -> dict[str, Any]:
    for key in ("request", "questionnaire", "profile", "input", "answers"):
        value = recommendation.get(key)

        if isinstance(value, dict):
            return value

    return recommendation


def _context_to_request(context: dict[str, Any]) -> RecommendationRequest:
    age = context.get("age")

    try:
        age_value = int(age) if age is not None else 24
    except (TypeError, ValueError):
        age_value = 24

    return RecommendationRequest(
        age=age_value,
        skin_type=str(context.get("skin_type") or "combination"),
        concerns=_string_list(context.get("concerns")),
        budget=str(context.get("budget") or "balanced"),
        excluded_ingredients=_string_list(context.get("excluded_ingredients")),
        custom_restrictions=_string_list(context.get("custom_restrictions")),
        experience=str(context.get("experience") or "guided"),
        values=_string_list(context.get("values")),
        anonymous_id=context.get("anonymous_id"),
    )


def _candidate_is_allowed(
    candidate: dict[str, Any],
    request: RecommendationRequest,
) -> bool:
    return product_filter_reason(candidate, request) is None


def _base_score(
    candidate: dict[str, Any],
    original_product: dict[str, Any],
    context: dict[str, Any],
) -> int:
    score = 0

    if _routine_step(candidate) == _routine_step(original_product):
        score += 50

    user_concerns = _lower_set(context.get("concerns"))
    if user_concerns:
        score += 7 * len(user_concerns.intersection(_concerns(candidate)))

    skin_type = str(context.get("skin_type") or "").lower()
    if skin_type and skin_type in _skin_types(candidate):
        score += 12

    user_values = _lower_set(context.get("values"))
    if user_values:
        score += 4 * len(user_values.intersection(_values(candidate)))

    candidate_price = _price(candidate)
    original_price = _price(original_product)

    if original_price and candidate_price:
        if candidate_price <= original_price:
            score += 5
        else:
            score -= min(15, int((candidate_price - original_price) / 300))

    score -= 4 * len(_risk_flags(candidate))

    return score


def _reason_bonus(
    candidate: dict[str, Any],
    original_product: dict[str, Any],
    reason: str,
) -> int:
    candidate_price = _price(candidate)
    original_price = _price(original_product)
    candidate_risks = _risk_flags(candidate)
    original_risks = _risk_flags(original_product)

    if reason == "too_expensive":
        if original_price and candidate_price < original_price:
            return 45 + min(25, int((original_price - candidate_price) / 200))
        return -25

    if reason == "dislikes_brand":
        return 45 if _brand(candidate) and _brand(candidate) != _brand(original_product) else -30

    if reason == "composition_concern":
        if len(candidate_risks) < len(original_risks):
            return 45

        if len(candidate_risks) == 0:
            return 35

        return -8 * len(candidate_risks)

    if reason == "texture_not_suitable":
        candidate_texture = _texture(candidate)
        original_texture = _texture(original_product)

        if candidate_texture and original_texture and candidate_texture != original_texture:
            return 45

        if candidate_texture and not original_texture:
            return 20

        return -10

    if reason == "too_many_steps":
        if candidate.get("is_basic") is True:
            return 35

        if candidate.get("routine_complexity") == "simple":
            return 30

        if _routine_step(candidate) == _routine_step(original_product):
            return 15

        return 0

    return 10


def _why_better(
    candidate: dict[str, Any],
    original_product: dict[str, Any],
    reason: str,
) -> str:
    name = candidate.get("name", "Средство")
    brand = candidate.get("brand", "бренд")

    candidate_price = _price(candidate)
    original_price = _price(original_product)

    if reason == "too_expensive" and candidate_price and original_price and candidate_price < original_price:
        return f"{name} от {brand} дешевле исходного средства и закрывает тот же шаг ухода."

    if reason == "dislikes_brand" and _brand(candidate) != _brand(original_product):
        return f"{name} от {brand} — альтернатива от другого бренда для того же шага."

    if reason == "composition_concern":
        risks = _risk_flags(candidate)

        if not risks:
            return f"{name} от {brand} отмечено как вариант без явных risk-флагов в текущем каталоге."

        return f"{name} от {brand} подобрано как вариант с более аккуратным профилем по составу."

    if reason == "texture_not_suitable":
        texture = candidate.get("texture") or candidate.get("format")

        if texture:
            return f"{name} от {brand} даёт альтернативную текстуру: {texture}."

        return f"{name} от {brand} — другой вариант для этого шага ухода."

    if reason == "too_many_steps":
        return f"{name} от {brand} оставляет тот же шаг ухода, но лучше подходит для более простой рутины."

    reason_label = REASON_LABELS.get(reason, REASON_LABELS["other"])
    return f"{name} от {brand} — {reason_label}, подобрана по тем же фильтрам безопасности."


def build_replacement_candidates(
    *,
    original_item: dict[str, Any],
    products: list[dict[str, Any]],
    reason: str,
    recommendation: dict[str, Any],
    limit: int = 4,
) -> list[dict[str, Any]]:
    original_product = original_item.get("product", original_item)
    original_id = _product_id(original_product)
    original_step = _routine_step(original_product)

    context = _recommendation_context(recommendation)
    request = _context_to_request(context)

    scored: list[tuple[int, dict[str, Any]]] = []

    for candidate in products:
        candidate_id = _product_id(candidate)

        if not candidate_id or candidate_id == original_id:
            continue

        if not _candidate_is_allowed(candidate, request):
            continue

        same_step = _routine_step(candidate) == original_step
        score = _base_score(candidate, original_product, context)
        score += _reason_bonus(candidate, original_product, reason)

        if same_step:
            score += 20
        else:
            score -= 25

        scored.append((score, candidate))

    scored.sort(
        key=lambda item: (
            item[0],
            -_price(item[1]) if reason == "too_expensive" else 0,
        ),
        reverse=True,
    )

    result: list[dict[str, Any]] = []

    for rank, (score, product) in enumerate(scored[:limit], start=1):
        reason_label = REASON_LABELS.get(reason, REASON_LABELS["other"])

        result.append(
            {
                "rank": rank,
                "product": product,
                "reason": reason,
                "replacement_score": score,
                "why_better": _why_better(product, original_product, reason),
                "replacement_reason": reason_label,
                "strategy_reason": reason_label,
            }
        )

    return result
''')


print("Step 4.3 filters and replacement strategy fixed successfully.")