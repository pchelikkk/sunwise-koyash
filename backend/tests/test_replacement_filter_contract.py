from app.algorithms.replacement_strategy import build_replacement_candidates


def _product(
    external_id: str,
    *,
    price: int,
    ingredients: list[str] | None = None,
    risk_flags: list[str] | None = None,
    ingredient_flags: list[str] | None = None,
) -> dict:
    return {
        "external_id": external_id,
        "name": external_id,
        "brand": "Test Brand",
        "category": "cleanser",
        "routine_step": "cleanser",
        "price_rub": price,
        "budget_segment": "balanced",
        "skin_types": ["combination"],
        "concerns": ["sebum"],
        "ingredients": ingredients or [],
        "ingredient_flags": ingredient_flags or [],
        "risk_flags": risk_flags or [],
        "texture": "gel",
        "is_active": True,
    }


def test_replacement_candidates_reuse_excluded_fragrance_filter() -> None:
    original = _product("original_cleanser", price=900)
    forbidden = _product(
        "cheap_fragrance_cleanser",
        price=300,
        ingredients=["fragrance"],
        risk_flags=["contains_fragrance"],
    )
    safe = _product(
        "safe_cleanser",
        price=650,
        ingredients=["glycerin"],
        ingredient_flags=["fragrance_free"],
    )

    candidates = build_replacement_candidates(
        original_item={"product": original},
        products=[original, forbidden, safe],
        reason="too_expensive",
        recommendation={
            "request": {
                "age": 24,
                "skin_type": "combination",
                "concerns": ["sebum"],
                "budget": "balanced",
                "excluded_ingredients": ["fragrance"],
                "custom_restrictions": [],
                "experience": "guided",
                "values": [],
                "anonymous_id": "replacement-filter-test",
            }
        },
    )

    candidate_ids = {candidate["product"]["external_id"] for candidate in candidates}

    assert "safe_cleanser" in candidate_ids
    assert "cheap_fragrance_cleanser" not in candidate_ids


def test_replacement_candidates_reuse_custom_alcohol_filter() -> None:
    original = _product("original_cleanser", price=900)
    forbidden = _product(
        "alcohol_cleanser",
        price=300,
        ingredients=["ethanol"],
    )
    safe = _product(
        "safe_cleanser",
        price=650,
        ingredients=["glycerin"],
    )

    candidates = build_replacement_candidates(
        original_item={"product": original},
        products=[original, forbidden, safe],
        reason="too_expensive",
        recommendation={
            "request": {
                "age": 24,
                "skin_type": "combination",
                "concerns": ["sebum"],
                "budget": "balanced",
                "excluded_ingredients": [],
                "custom_restrictions": ["спирт"],
                "experience": "guided",
                "values": [],
                "anonymous_id": "replacement-filter-test",
            }
        },
    )

    candidate_ids = {candidate["product"]["external_id"] for candidate in candidates}

    assert "safe_cleanser" in candidate_ids
    assert "alcohol_cleanser" not in candidate_ids
