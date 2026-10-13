from dataclasses import dataclass

from app.schemas.recommendation import RecommendationRequest, ScoreBreakdown

CORE_STEPS = {"cleanser", "moisturizer", "spf"}
TARGETED_STEPS = {"serum", "toner", "treatment", "mask"}
IRRITANT_RISK_FLAGS = {
    "contains_alcohol",
    "contains_essential_oils",
    "contains_fragrance",
}


@dataclass(frozen=True)
class ScoredProduct:
    product: dict
    score: ScoreBreakdown


def _budget_score(user_budget: str, product_budget: str) -> tuple[int, int]:
    if user_budget == product_budget:
        return 15, 3

    if user_budget == "balanced" and product_budget in {"minimum", "balanced"}:
        return 12, 2

    if user_budget == "premium" and product_budget in {"balanced", "premium"}:
        return 10, 1

    if user_budget == "minimum" and product_budget == "balanced":
        return 5, 0

    return 0, -1


def _texture_group(value: str | None) -> str | None:
    normalized = str(value or "").strip().lower().replace("ё", "е")

    if not normalized:
        return None

    if any(
        marker in normalized
        for marker in ("rich", "плотн", "густ", "пит", "ночн", "паста")
    ):
        return "rich"

    if "крем" in normalized or "cream" in normalized:
        return "cream"

    if any(
        marker in normalized
        for marker in (
            "gel",
            "liquid",
            "serum",
            "toner",
            "гель",
            "жидк",
            "лосьон",
            "пен",
            "сыворот",
            "тонер",
            "эссен",
            "спрей",
        )
    ):
        return "lightweight"

    return None


def _sensitivity_scores(
    request: RecommendationRequest,
    risk_flags: set[str],
) -> tuple[int, int]:
    irritants = risk_flags.intersection(IRRITANT_RISK_FLAGS)
    level = request.sensitivity_level

    if request.skin_type == "sensitive" and level == "unknown":
        level = "high"

    if level == "high":
        return (8, 0) if not irritants else (0, -20)

    if level == "medium":
        return (4, 0) if not irritants else (0, -4 * len(irritants))

    return 0, 0


def _routine_preference_score(step: str, preference: str) -> int:
    if preference == "minimal":
        return 5 if step in CORE_STEPS else 0

    if preference == "complete":
        return 5 if step in TARGETED_STEPS else 1

    return 3 if step in CORE_STEPS | {"serum", "toner"} else 0


def score_product(product: dict, request: RecommendationRequest) -> ScoreBreakdown:
    product_concerns = set(product.get("concerns", []))
    user_concerns = set(request.concerns)
    matched_concerns = product_concerns.intersection(user_concerns)
    step = str(product.get("routine_step") or "")

    routine_step_score = 30
    concern_score = min(25, len(matched_concerns) * 10)
    primary_concern_score = (
        7 if request.primary_concern in product_concerns else 0
    )

    product_skin_types = set(product.get("skin_types", []))
    if request.skin_type in product_skin_types:
        skin_type_score = 20
    elif "all" in product_skin_types:
        skin_type_score = 10
    else:
        skin_type_score = 0

    budget_score, _ = _budget_score(
        user_budget=request.budget,
        product_budget=product.get("budget_segment", ""),
    )

    risk_flags = set(product.get("risk_flags", []))
    substantive_risks = risk_flags - {"sensitive_attention"}
    ingredient_flags = set(product.get("ingredient_flags", []))
    product_values = set(product.get("values", []))

    experience_score = 0
    penalties = 0

    if request.experience in {"beginner", "minimal"}:
        if substantive_risks:
            penalties -= 8
        else:
            experience_score += 8
    elif request.experience in {"basic", "guided"} and not substantive_risks:
        experience_score += 3
    elif request.experience == "advanced" and step in {"treatment", "mask"}:
        experience_score += 6

    safety_score = 0
    if "fragrance_free" in ingredient_flags:
        safety_score += 5
    if "alcohol_free" in ingredient_flags:
        safety_score += 5

    sensitivity_score, sensitivity_penalty = _sensitivity_scores(
        request,
        risk_flags,
    )
    penalties += sensitivity_penalty

    values_score = min(15, 5 * len(set(request.values).intersection(product_values)))
    if (
        "price_quality" in request.values
        and product.get("budget_segment") in {"minimum", "balanced"}
    ):
        values_score += 3

    texture_score = 0
    if request.texture_preference != "no_preference":
        if _texture_group(product.get("texture")) == request.texture_preference:
            texture_score = 6

    routine_preference_score = _routine_preference_score(
        step,
        request.routine_preference,
    )

    if request.budget == "minimum" and product.get("budget_segment") == "premium":
        penalties -= 20

    total = (
        routine_step_score
        + concern_score
        + primary_concern_score
        + skin_type_score
        + budget_score
        + experience_score
        + safety_score
        + sensitivity_score
        + texture_score
        + routine_preference_score
        + values_score
        + penalties
    )

    return ScoreBreakdown(
        routine_step_score=routine_step_score,
        concern_score=concern_score,
        primary_concern_score=primary_concern_score,
        skin_type_score=skin_type_score,
        budget_score=budget_score,
        experience_score=experience_score,
        safety_score=safety_score,
        sensitivity_score=sensitivity_score,
        texture_score=texture_score,
        routine_preference_score=routine_preference_score,
        values_score=values_score,
        penalties=penalties,
        total=total,
    )


def score_products(
    products: list[dict],
    request: RecommendationRequest,
) -> list[ScoredProduct]:
    return [
        ScoredProduct(product=product, score=score_product(product, request))
        for product in products
    ]
