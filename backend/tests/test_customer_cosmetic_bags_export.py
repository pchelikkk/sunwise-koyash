from scripts.export_customer_cosmetic_bags import (
    _convert_routine_part,
    _enrich_product_from_dataset,
    _ingredients_for_llm,
    _quality_issues,
    _quality_warnings,
    _unique_cosmetic_bag_products,
)


def _dataset_product(product_id: str = "product_001") -> dict:
    return {
        "external_id": product_id,
        "name": "Dataset Serum",
        "brand": "Dataset Brand",
        "routine_step": "serum",
        "ingredients": ["niacinamide"],
        "key_ingredients": ["niacinamide", "zinc"],
        "concerns": ["sebum"],
        "risk_flags": [],
        "source": "dataset",
    }


def test_ingredients_for_llm_prefers_key_ingredients() -> None:
    product = {
        "ingredients": ["water", "glycerin", "panthenol"],
        "key_ingredients": ["niacinamide", "zinc"],
    }

    assert _ingredients_for_llm(product) == "niacinamide, zinc"


def test_enrich_product_from_dataset_makes_dataset_provenance_explicit() -> None:
    api_product = {
        "external_id": "product_001",
        "name": "Short API Name",
        "brand": "Short API Brand",
    }
    enriched = _enrich_product_from_dataset(
        api_product,
        {"product_001": _dataset_product("product_001")},
    )

    assert enriched["name"] == "Dataset Serum"
    assert enriched["source"] == "dataset"
    assert enriched["dataset_verified"] is True
    assert enriched["dataset_external_id"] == "product_001"


def test_enrich_product_from_dataset_marks_missing_product_unverified() -> None:
    enriched = _enrich_product_from_dataset(
        {"external_id": "missing_product", "name": "Missing"},
        {"product_001": _dataset_product("product_001")},
    )

    assert enriched["dataset_verified"] is False
    assert enriched["dataset_external_id"] == "missing_product"


def test_convert_routine_part_builds_llm_context_from_dataset_product() -> None:
    item = {
        "routine_step": "serum",
        "score": 88,
        "matched_concerns": ["sebum"],
        "why_here": "Тестовое объяснение.",
        "product": {
            "external_id": "product_001",
            "name": "Short API Name",
            "brand": "Short API Brand",
        },
    }

    result = _convert_routine_part(
        part="evening",
        items=[item],
        scenario_input={
            "skin_type": "combination",
            "concerns": ["sebum", "acne"],
        },
        dataset_by_external_id={"product_001": _dataset_product("product_001")},
    )

    assert result[0]["concern_match"] == 1
    assert result[0]["product"]["source"] == "dataset"
    assert result[0]["product"]["dataset_verified"] is True
    assert result[0]["llm_user_prompt_context"]["skin_type"] == "combination"
    assert result[0]["llm_user_prompt_context"]["matched_concerns"] == ["sebum"]
    assert result[0]["llm_user_prompt_context"]["name"] == "Dataset Serum"
    assert result[0]["llm_user_prompt_context"]["step"] == "сыворотка"


def test_quality_issues_detects_product_not_in_dataset() -> None:
    payload = {
        "routine": {
            "morning": [
                {
                    "product": {
                        "external_id": "missing_product",
                        "brand": "Dataset Brand",
                    }
                },
            ],
            "evening": [],
        }
    }

    issues = _quality_issues(payload, {"product_001": _dataset_product("product_001")})

    assert issues == ["not_in_dataset:missing_product"]


def test_quality_issues_detects_sample_brands_as_fatal() -> None:
    payload = {
        "routine": {
            "morning": [
                {
                    "product": {
                        "external_id": "cleanser_001",
                        "brand": "Koyash Sample",
                    }
                },
            ],
            "evening": [],
        }
    }

    issues = _quality_issues(payload, {"cleanser_001": _dataset_product("cleanser_001")})

    assert "sample_brand_returned:Koyash Sample:cleanser_001" in issues


def test_schedule_duplicate_is_warning_not_fatal_issue() -> None:
    payload = {
        "routine": {
            "morning": [
                {
                    "product": {
                        "external_id": "product_001",
                        "brand": "Dataset Brand",
                    }
                },
            ],
            "evening": [
                {
                    "product": {
                        "external_id": "product_001",
                        "brand": "Dataset Brand",
                    }
                },
            ],
        }
    }

    assert _quality_issues(payload, {"product_001": _dataset_product("product_001")}) == []
    assert _quality_warnings(payload) == ["product_reused_in_schedule:product_001"]


def test_unique_cosmetic_bag_products_deduplicates_schedule_items_and_uses_dataset() -> None:
    product = {
        "external_id": "product_001",
        "name": "Short API Name",
        "brand": "Short API Brand",
    }

    routine = {
        "morning": [{"product": product}],
        "evening": [{"product": product}],
    }

    unique_products = _unique_cosmetic_bag_products(
        routine,
        {"product_001": _dataset_product("product_001")},
    )

    assert len(unique_products) == 1
    assert unique_products[0]["external_id"] == "product_001"
    assert unique_products[0]["source"] == "dataset"
    assert unique_products[0]["dataset_verified"] is True
