from pathlib import Path

ROOT = Path(r"C:\Projects\sunwise-koyash")


def write_file(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")


write_file("backend/app/algorithms/replacement_strategy.py", r'''
import re
from typing import Any

from app.algorithms.filters import product_filter_reason
from app.schemas.recommendation import RecommendationRequest


MAX_REPLACEMENT_CANDIDATES = 3
MIN_REPLACEMENT_SCORE = 45


SAMPLE_BRANDS = {
    "Koyash Sample",
    "Soft Lab",
    "Clear Skin",
    "Sun Basic",
}


SAFE_FLAGS = {
    "fragrance_free",
    "alcohol_free",
    "без отдушек",
    "без отдушки",
    "без спирта",
}


RISK_FIELDS = (
    "risk_flags",
    "ingredient_flags",
    "excluded_ingredient_flags",
    "avoid_if",
    "allergens",
    "issues",
)


REASON_LABELS = {
    "too_expensive": "дешевле и закрывает тот же шаг ухода",
    "dislikes_brand": "другой бренд для того же шага ухода",
    "composition_concern": "более спокойный вариант по составу",
    "texture_not_suitable": "другая текстура для того же шага ухода",
    "too_many_steps": "более простой вариант для того же шага ухода",
    "other": "альтернатива по тем же правилам подбора",
}


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


def _text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _normalized_text(value: Any) -> str:
    text = _text(value).lower()
    text = text.replace("ё", "е")
    text = re.sub(r"[\s\-_./:;()]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _product_id(product: dict[str, Any]) -> str:
    return str(
        product.get("external_id")
        or product.get("product_external_id")
        or product.get("product_id")
        or product.get("_id")
        or ""
    ).strip()


def _price(product: dict[str, Any]) -> int:
    try:
        return int(product.get("price_rub") or 0)
    except (TypeError, ValueError):
        return 0


def _brand(product: dict[str, Any]) -> str:
    return _normalized_text(product.get("brand"))


def _routine_step(product: dict[str, Any]) -> str:
    return _normalized_text(product.get("routine_step") or product.get("step"))


def _texture(product: dict[str, Any]) -> str:
    return _normalized_text(
        product.get("texture")
        or product.get("format")
        or product.get("product_format")
    )


def _concerns(product: dict[str, Any]) -> set[str]:
    return _lower_set(product.get("concerns")) | _lower_set(product.get("matched_concerns"))


def _skin_types(product: dict[str, Any]) -> set[str]:
    return _lower_set(product.get("skin_types")) | _lower_set(product.get("suitable_skin_types"))


def _values(product: dict[str, Any]) -> set[str]:
    return _lower_set(product.get("values")) | _lower_set(product.get("tags"))


def _raw_risk_values(product: dict[str, Any]) -> set[str]:
    values: set[str] = set()

    for field in RISK_FIELDS:
        raw = product.get(field)

        if isinstance(raw, list):
            values.update(_lower_set(raw))
        elif raw:
            values.add(_normalized_text(raw))

    return values


def _risk_flags(product: dict[str, Any]) -> set[str]:
    raw_values = _raw_risk_values(product)
    risks = set()

    for value in raw_values:
        if not value or value in SAFE_FLAGS:
            continue

        if value.startswith("fragrance free") or value.startswith("alcohol free"):
            continue

        if value in {
            "contains fragrance",
            "contains_fragrance",
            "fragrance",
            "parfum",
            "perfume",
            "contains alcohol",
            "contains_alcohol",
            "drying alcohol",
            "drying_alcohol",
            "alcohol denat",
            "denatured alcohol",
            "contains essential oils",
            "contains_essential_oils",
            "essential oils",
            "essential oil",
            "phototoxic components",
            "phototoxic_components",
            "sensitive attention",
            "sensitive_attention",
        }:
            risks.add(value)
            continue

        if any(
            marker in value
            for marker in (
                "отдуш",
                "alcohol denat",
                "denatured alcohol",
                "essential oil",
                "эфирн",
                "фототокс",
            )
        ):
            risks.add(value)

    return risks


def _risk_burden(product: dict[str, Any]) -> int:
    return len(_risk_flags(product))


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


def _extract_product_from_routine_item(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None

    product = item.get("product")

    if isinstance(product, dict):
        return product

    if "external_id" in item or "product_external_id" in item:
        return item

    return None


def _current_routine_product_ids(recommendation: dict[str, Any]) -> set[str]:
    routine = recommendation.get("routine")

    if not isinstance(routine, dict):
        return set()

    result: set[str] = set()

    for part in ("morning", "evening"):
        for item in routine.get(part, []) or []:
            product = _extract_product_from_routine_item(item)

            if product is None:
                continue

            product_id = _product_id(product)

            if product_id:
                result.add(product_id)

    return result


def _product_source_is_allowed(product: dict[str, Any]) -> bool:
    source = _normalized_text(product.get("source"))
    brand = _text(product.get("brand"))

    if source in {"sample", "demo"}:
        return False

    if brand in SAMPLE_BRANDS:
        return False

    return True


def _same_replacement_step(candidate: dict[str, Any], original_product: dict[str, Any]) -> bool:
    original_step = _routine_step(original_product)
    candidate_step = _routine_step(candidate)

    if not original_step or not candidate_step:
        return False

    return candidate_step == original_step


def _candidate_is_allowed(
    candidate: dict[str, Any],
    request: RecommendationRequest,
) -> bool:
    if not _product_source_is_allowed(candidate):
        return False

    return product_filter_reason(candidate, request) is None


def _eligible_by_reason(
    candidate: dict[str, Any],
    original_product: dict[str, Any],
    reason: str,
) -> bool:
    candidate_price = _price(candidate)
    original_price = _price(original_product)

    if reason == "too_expensive":
        if original_price > 0 and candidate_price > 0:
            return candidate_price < original_price
        return True

    if reason == "dislikes_brand":
        candidate_brand = _brand(candidate)
        original_brand = _brand(original_product)

        if candidate_brand and original_brand:
            return candidate_brand != original_brand

        return True

    if reason == "composition_concern":
        original_risk = _risk_burden(original_product)
        candidate_risk = _risk_burden(candidate)

        if original_risk > 0:
            return candidate_risk < original_risk

        return candidate_risk == 0

    if reason == "texture_not_suitable":
        candidate_texture = _texture(candidate)
        original_texture = _texture(original_product)

        if candidate_texture and original_texture:
            return candidate_texture != original_texture

        return True

    if reason == "too_many_steps":
        complexity = _normalized_text(candidate.get("routine_complexity"))
        is_basic = candidate.get("is_basic")

        if complexity and complexity not in {"simple", "basic", "minimal"}:
            return False

        if is_basic is False:
            return False

        return True

    return True


def _base_score(
    candidate: dict[str, Any],
    original_product: dict[str, Any],
    context: dict[str, Any],
) -> int:
    score = 0

    if _same_replacement_step(candidate, original_product):
        score += 50

    user_concerns = _lower_set(context.get("concerns"))
    candidate_concerns = _concerns(candidate)

    if user_concerns:
        score += 10 * len(user_concerns.intersection(candidate_concerns))

    skin_type = str(context.get("skin_type") or "").lower()
    candidate_skin_types = _skin_types(candidate)

    if skin_type and (skin_type in candidate_skin_types or "all" in candidate_skin_types):
        score += 12

    user_values = _lower_set(context.get("values"))
    candidate_values = _values(candidate)

    if user_values:
        score += 4 * len(user_values.intersection(candidate_values))

    candidate_price = _price(candidate)
    original_price = _price(original_product)

    if original_price and candidate_price:
        if candidate_price <= original_price:
            score += 8
        else:
            score -= min(25, int((candidate_price - original_price) / 200))

    score -= 8 * _risk_burden(candidate)

    return score


def _reason_bonus(
    candidate: dict[str, Any],
    original_product: dict[str, Any],
    reason: str,
) -> int:
    candidate_price = _price(candidate)
    original_price = _price(original_product)

    if reason == "too_expensive":
        if original_price and candidate_price and candidate_price < original_price:
            return 45 + min(25, int((original_price - candidate_price) / 200))
        return -100

    if reason == "dislikes_brand":
        return 45 if _brand(candidate) != _brand(original_product) else -100

    if reason == "composition_concern":
        original_risk = _risk_burden(original_product)
        candidate_risk = _risk_burden(candidate)

        if original_risk > 0 and candidate_risk < original_risk:
            return 45 + 10 * (original_risk - candidate_risk)

        if original_risk == 0 and candidate_risk == 0:
            return 25

        return -100

    if reason == "texture_not_suitable":
        candidate_texture = _texture(candidate)
        original_texture = _texture(original_product)

        if candidate_texture and original_texture and candidate_texture != original_texture:
            return 45

        if candidate_texture and not original_texture:
            return 20

        return -100

    if reason == "too_many_steps":
        complexity = _normalized_text(candidate.get("routine_complexity"))
        is_basic = candidate.get("is_basic")

        if is_basic is True:
            return 35

        if complexity in {"simple", "basic", "minimal"}:
            return 35

        return 15

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

    if reason == "too_expensive" and candidate_price and original_price:
        return (
            f"{name} от {brand} дешевле исходного средства "
            f"и закрывает тот же шаг ухода."
        )

    if reason == "dislikes_brand":
        return f"{name} от {brand} — альтернатива от другого бренда для того же шага."

    if reason == "composition_concern":
        return f"{name} от {brand} проходит те же ограничения и выглядит спокойнее по risk-флагам."

    if reason == "texture_not_suitable":
        texture = candidate.get("texture") or candidate.get("format")

        if texture:
            return f"{name} от {brand} закрывает тот же шаг, но в другой текстуре: {texture}."

        return f"{name} от {brand} — другой вариант для того же шага ухода."

    if reason == "too_many_steps":
        return f"{name} от {brand} закрывает тот же шаг и не добавляет лишний этап в рутину."

    return f"{name} от {brand} подобрано как альтернатива по тем же фильтрам."


def build_replacement_candidates(
    *,
    original_item: dict[str, Any],
    products: list[dict[str, Any]],
    reason: str,
    recommendation: dict[str, Any],
    limit: int = MAX_REPLACEMENT_CANDIDATES,
) -> list[dict[str, Any]]:
    original_product = original_item.get("product", original_item)
    original_id = _product_id(original_product)

    context = _recommendation_context(recommendation)
    request = _context_to_request(context)
    current_routine_ids = _current_routine_product_ids(recommendation)

    max_candidates = max(0, min(int(limit or MAX_REPLACEMENT_CANDIDATES), MAX_REPLACEMENT_CANDIDATES))
    scored: list[dict[str, Any]] = []

    for candidate in products:
        candidate_id = _product_id(candidate)

        if not candidate_id:
            continue

        if candidate_id == original_id:
            continue

        if candidate_id in current_routine_ids:
            continue

        if not _same_replacement_step(candidate, original_product):
            continue

        if not _candidate_is_allowed(candidate, request):
            continue

        if not _eligible_by_reason(candidate, original_product, reason):
            continue

        score = _base_score(candidate, original_product, context)
        score += _reason_bonus(candidate, original_product, reason)

        if score < MIN_REPLACEMENT_SCORE:
            continue

        reason_label = REASON_LABELS.get(reason, REASON_LABELS["other"])

        scored.append(
            {
                "rank": 0,
                "product": candidate,
                "reason": reason,
                "replacement_score": score,
                "why_better": _why_better(candidate, original_product, reason),
                "replacement_reason": reason_label,
                "strategy_reason": reason_label,
            }
        )

    scored.sort(
        key=lambda item: (
            -int(item["replacement_score"]),
            _price(item["product"]) if reason == "too_expensive" else 0,
            _product_id(item["product"]),
        )
    )

    result = scored[:max_candidates]

    for index, item in enumerate(result, start=1):
        item["rank"] = index

    return result
''')


write_file("backend/tests/test_replacement_strict_contract.py", r'''
from app.algorithms.replacement_strategy import build_replacement_candidates


def _product(
    external_id: str,
    *,
    routine_step: str = "cleanser",
    price: int = 700,
    brand: str = "Brand",
    texture: str = "gel",
    concerns: list[str] | None = None,
    skin_types: list[str] | None = None,
    values: list[str] | None = None,
    risk_flags: list[str] | None = None,
    ingredient_flags: list[str] | None = None,
    source: str = "dataset",
    is_basic: bool | None = True,
    routine_complexity: str | None = "simple",
) -> dict:
    product = {
        "external_id": external_id,
        "name": external_id,
        "brand": brand,
        "category": routine_step,
        "routine_step": routine_step,
        "price_rub": price,
        "budget_segment": "balanced",
        "skin_types": skin_types or ["all", "combination"],
        "concerns": concerns or ["sebum", "acne"],
        "ingredients": ["glycerin"],
        "ingredient_flags": ingredient_flags or ["fragrance_free", "alcohol_free"],
        "risk_flags": risk_flags or [],
        "values": values or ["comfort", "price_quality"],
        "texture": texture,
        "is_active": True,
        "source": source,
    }

    if is_basic is not None:
        product["is_basic"] = is_basic

    if routine_complexity is not None:
        product["routine_complexity"] = routine_complexity

    return product


def _recommendation(extra_routine_product: dict | None = None) -> dict:
    morning = []

    if extra_routine_product is not None:
        morning.append({"product": extra_routine_product})

    return {
        "request": {
            "age": 24,
            "skin_type": "combination",
            "concerns": ["sebum", "acne"],
            "budget": "balanced",
            "excluded_ingredients": [],
            "custom_restrictions": [],
            "experience": "guided",
            "values": ["comfort", "price_quality"],
            "anonymous_id": "strict-replacement-test",
        },
        "routine": {
            "morning": morning,
            "evening": [],
        },
    }


def test_replacements_do_not_include_products_already_in_routine() -> None:
    original = _product("original_cleanser", price=1000, brand="A")
    already_in_bag = _product("already_in_bag", price=650, brand="B")
    valid = _product("valid_replacement", price=600, brand="C")

    candidates = build_replacement_candidates(
        original_item={"product": original},
        products=[original, already_in_bag, valid],
        reason="too_expensive",
        recommendation=_recommendation(extra_routine_product=already_in_bag),
    )

    ids = [item["product"]["external_id"] for item in candidates]

    assert ids == ["valid_replacement"]


def test_replacements_never_use_other_routine_step_as_filler() -> None:
    original = _product("original_cleanser", routine_step="cleanser", price=1000)
    serum = _product("serum_candidate", routine_step="serum", price=300)

    candidates = build_replacement_candidates(
        original_item={"product": original},
        products=[original, serum],
        reason="too_expensive",
        recommendation=_recommendation(),
    )

    assert candidates == []


def test_too_expensive_returns_up_to_three_good_cheaper_candidates_only() -> None:
    original = _product("original_cleanser", price=1200)
    cheap_1 = _product("cheap_1", price=500)
    cheap_2 = _product("cheap_2", price=650)
    cheap_3 = _product("cheap_3", price=800)
    expensive = _product("expensive", price=1400)

    candidates = build_replacement_candidates(
        original_item={"product": original},
        products=[original, cheap_1, cheap_2, cheap_3, expensive],
        reason="too_expensive",
        recommendation=_recommendation(),
        limit=4,
    )

    ids = [item["product"]["external_id"] for item in candidates]

    assert ids == ["cheap_1", "cheap_2", "cheap_3"]
    assert len(candidates) == 3
    assert all(item["product"]["price_rub"] < original["price_rub"] for item in candidates)


def test_dislikes_brand_requires_another_brand() -> None:
    original = _product("original_cleanser", brand="Same Brand")
    same_brand = _product("same_brand", brand="Same Brand")
    another_brand = _product("another_brand", brand="Another Brand")

    candidates = build_replacement_candidates(
        original_item={"product": original},
        products=[original, same_brand, another_brand],
        reason="dislikes_brand",
        recommendation=_recommendation(),
    )

    ids = [item["product"]["external_id"] for item in candidates]

    assert ids == ["another_brand"]


def test_composition_concern_does_not_return_riskier_candidate() -> None:
    original = _product(
        "original_cleanser",
        risk_flags=["contains_fragrance", "contains_essential_oils"],
    )
    safe = _product("safe_cleanser", risk_flags=[])
    still_risky = _product("still_risky", risk_flags=["contains_fragrance"])

    candidates = build_replacement_candidates(
        original_item={"product": original},
        products=[original, safe, still_risky],
        reason="composition_concern",
        recommendation=_recommendation(),
    )

    ids = [item["product"]["external_id"] for item in candidates]

    assert ids[0] == "safe_cleanser"
    assert "still_risky" in ids
    assert all(
        len(item["product"].get("risk_flags", [])) < len(original.get("risk_flags", []))
        for item in candidates
    )


def test_texture_not_suitable_requires_different_texture_when_known() -> None:
    original = _product("original_cleanser", texture="foam")
    same_texture = _product("same_texture", texture="foam")
    different_texture = _product("different_texture", texture="gel")

    candidates = build_replacement_candidates(
        original_item={"product": original},
        products=[original, same_texture, different_texture],
        reason="texture_not_suitable",
        recommendation=_recommendation(),
    )

    ids = [item["product"]["external_id"] for item in candidates]

    assert ids == ["different_texture"]
''')


print("Step 4.6 strict replacement files written successfully.")