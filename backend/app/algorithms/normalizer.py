from app.schemas.recommendation import RecommendationRequest

RESTRICTION_ALIASES = {
    "отдушка": "fragrance",
    "отдушки": "fragrance",
    "ароматизатор": "fragrance",
    "ароматизаторы": "fragrance",
    "fragrance": "fragrance",
    "parfum": "fragrance",
    "perfume": "fragrance",
    "спирт": "alcohol",
    "алкоголь": "alcohol",
    "alcohol": "alcohol",
    "ethanol": "alcohol",
    "этанол": "alcohol",
    "ethyl alcohol": "alcohol",
    "эфирные масла": "essential_oils",
    "эфирное масло": "essential_oils",
    "essential oils": "essential_oils",
    "essential oil": "essential_oils",
    "нет ограничений": "none",
    "ничего": "none",
    "none": "none",
    "no restrictions": "none",
    "затрудняюсь ответить": "unknown",
    "unknown": "unknown",
}

CONCERN_ALIASES = {
    "reactivity": "reactivity",
    "sensitivity": "reactivity",
    "sensitive": "reactivity",
    "реактивность": "reactivity",
    "чувствительность": "reactivity",
    "чувствительная кожа": "reactivity",
    "unknown": "unknown",
    "затрудняюсь ответить": "unknown",
    "пока не знаю": "unknown",
}

VALUE_ALIASES = {
    "price": "price_quality",
    "quality": "price_quality",
    "simple_routine": "minimal_steps",
    "minimal_steps": "minimal_steps",
    "unknown": "unknown",
    "затрудняюсь ответить": "unknown",
}


EXPERIENCE_ALIASES = {
    "guided": "guided",
    "beginner": "beginner",
    "basic": "basic",
    "advanced": "advanced",
    "minimal": "minimal",
}


def normalize_text(value: str) -> str:
    return value.strip().lower().replace("ё", "е")


def _unique_without_empty(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


def normalize_restriction(value: str) -> str:
    normalized = normalize_text(value)
    return RESTRICTION_ALIASES.get(normalized, normalized)


def normalize_values(values: list[str], aliases: dict[str, str] | None = None) -> list[str]:
    aliases = aliases or {}
    normalized_values = []

    for value in values:
        normalized = normalize_text(value)
        normalized = aliases.get(normalized, normalized)
        if normalized not in {"", "unknown"}:
            normalized_values.append(normalized)

    return _unique_without_empty(normalized_values)


def normalize_restrictions(values: list[str]) -> list[str]:
    result = []
    for value in values:
        normalized = normalize_restriction(value)
        if normalized and normalized not in {"none", "unknown"} and normalized not in result:
            result.append(normalized)
    return result


def normalize_experience(value: str) -> str:
    normalized = normalize_text(value)
    return EXPERIENCE_ALIASES.get(normalized, normalized)


def normalized_request(request: RecommendationRequest) -> RecommendationRequest:
    concerns = normalize_values(request.concerns, CONCERN_ALIASES)
    values = normalize_values(request.values, VALUE_ALIASES)
    primary_concern_values = normalize_values(
        [request.primary_concern] if request.primary_concern else [],
        CONCERN_ALIASES,
    )
    primary_concern = primary_concern_values[0] if primary_concern_values else None

    if primary_concern and primary_concern not in concerns:
        concerns.insert(0, primary_concern)

    routine_preference = normalize_text(request.routine_preference)
    if routine_preference == "balanced" and "minimal_steps" in values:
        routine_preference = "minimal"

    return RecommendationRequest(
        age=request.age,
        skin_type=normalize_text(request.skin_type),
        concerns=concerns,
        primary_concern=primary_concern,
        sensitivity_level=normalize_text(request.sensitivity_level),
        budget=normalize_text(request.budget),
        excluded_ingredients=normalize_restrictions(request.excluded_ingredients),
        custom_restrictions=normalize_restrictions(request.custom_restrictions),
        experience=normalize_experience(request.experience),
        routine_preference=routine_preference,
        texture_preference=normalize_text(request.texture_preference),
        values=values,
        skin_diagnostic_answers=request.skin_diagnostic_answers,
        anonymous_id=request.anonymous_id,
    )


def product_tokens(product: dict) -> set[str]:
    values: list[str] = []

    for key in ["ingredients", "ingredient_flags", "risk_flags"]:
        values.extend(product.get(key, []))

    values.extend(
        [
            product.get("category", ""),
            product.get("routine_step", ""),
            product.get("texture", "") or "",
        ]
    )

    return {normalize_restriction(value) for value in values if value}
