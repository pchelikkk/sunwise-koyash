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
