from typing import Any

from app.algorithms.scoring import ScoredProduct
from app.schemas.recommendation import RecommendationRequest

CONCERN_LABELS = {
    "acne": "высыпания",
    "sebum": "жирный блеск",
    "dryness": "сухость",
    "post_acne": "постакне",
    "uneven_tone": "неровный тон",
    "sensitivity": "реактивность / чувствительность",
    "reactivity": "реактивность",
    "age_changes": "возрастные изменения",
    "unknown": "затрудняюсь ответить",
}


def matched_concern_labels(product: dict, request: RecommendationRequest) -> list[str]:
    matched = set(product.get("concerns", [])).intersection(set(request.concerns))
    return [CONCERN_LABELS.get(item, item) for item in sorted(matched)]


def build_llm_context(
    item: ScoredProduct,
    request: RecommendationRequest,
    why_here: str,
    safety_note: str,
) -> dict[str, Any]:
    product = item.product

    return {
        "tone": "warm, caring, simple, KOYASH voice: бабушка + ИИ",
        "instruction": (
            "Rewrite only the explanation text. Do not change product facts or "
            "safety filters."
        ),
        "user_profile": {
            "age": request.age,
            "skin_type": request.skin_type,
            "concerns": request.concerns,
            "primary_concern": request.primary_concern,
            "sensitivity_level": request.sensitivity_level,
            "budget": request.budget,
            "experience": request.experience,
            "routine_preference": request.routine_preference,
            "texture_preference": request.texture_preference,
            "values": request.values,
            "excluded_ingredients": (
                request.excluded_ingredients + request.custom_restrictions
            ),
        },
        "product_facts": {
            "external_id": product.get("external_id"),
            "name": product.get("name"),
            "brand": product.get("brand"),
            "routine_step": product.get("routine_step"),
            "price_rub": product.get("price_rub"),
            "ingredients": product.get("ingredients", []),
            "ingredient_flags": product.get("ingredient_flags", []),
            "risk_flags": product.get("risk_flags", []),
        },
        "deterministic_explanation": {
            "why_here": why_here,
            "safety_note": safety_note,
            "score_breakdown": item.score.model_dump(),
        },
    }
