import argparse
import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from pymongo import AsyncMongoClient

from app.core.config import get_settings

API_BASE_URL = os.environ.get("KOYASH_API_BASE_URL", "http://127.0.0.1:8000/api/v1")


SAMPLE_BRANDS = {
    "Koyash Sample",
    "Soft Lab",
    "Clear Skin",
    "Sun Basic",
    "KOYASH Test",
}


SAMPLE_PRODUCTS_QUERY: dict[str, Any] = {
    "$or": [
        {"source": {"$ne": "dataset"}},
        {"source": None},
        {"source": {"$exists": False}},
        {"source": {"$in": ["sample", "demo", "test"]}},
        {"brand": {"$in": sorted(SAMPLE_BRANDS)}},
        {
            "external_id": {
                "$regex": "sample|cleanser_00|serum_00|moisturizer_00|spf_00",
                "$options": "i",
            }
        },
    ]
}


DATASET_PRODUCT_FIELDS = {
    "_id": 0,
    "external_id": 1,
    "name": 1,
    "brand": 1,
    "category": 1,
    "routine_step": 1,
    "price_rub": 1,
    "currency": 1,
    "budget_segment": 1,
    "skin_types": 1,
    "concerns": 1,
    "ingredients": 1,
    "key_ingredients": 1,
    "ingredient_highlights": 1,
    "functional_category": 1,
    "risk_flags": 1,
    "ingredient_flags": 1,
    "texture": 1,
    "format": 1,
    "product_url": 1,
    "image_url": 1,
    "source": 1,
    "is_active": 1,
}


SCENARIOS = [
    {
        "id": "combination_acne_sebum_no_fragrance",
        "title": "Комбинированная кожа, высыпания и жирный блеск, без отдушек",
        "input": {
            "age": 24,
            "skin_type": "combination",
            "concerns": ["acne", "sebum"],
            "budget": "balanced",
            "excluded_ingredients": ["fragrance"],
            "custom_restrictions": [],
            "experience": "guided",
            "values": ["comfort", "price_quality"],
            "anonymous_id": "customer-export-01",
        },
    },
    {
        "id": "sensitive_reactivity_no_fragrance_no_alcohol",
        "title": "Чувствительная кожа, реактивность, без отдушек и спирта",
        "input": {
            "age": 27,
            "skin_type": "sensitive",
            "concerns": ["reactivity", "redness"],
            "budget": "balanced",
            "excluded_ingredients": ["fragrance", "alcohol"],
            "custom_restrictions": [],
            "experience": "guided",
            "values": ["comfort", "soft_formula"],
            "anonymous_id": "customer-export-02",
        },
    },
    {
        "id": "dry_dehydration_minimum_budget",
        "title": "Сухая кожа, сухость и обезвоженность, минимальный бюджет",
        "input": {
            "age": 31,
            "skin_type": "dry",
            "concerns": ["dryness", "dehydration"],
            "budget": "minimum",
            "excluded_ingredients": [],
            "custom_restrictions": [],
            "experience": "guided",
            "values": ["price", "comfort"],
            "anonymous_id": "customer-export-03",
        },
    },
    {
        "id": "oily_acne_sebum_minimum_budget",
        "title": "Жирная кожа, высыпания и себум, минимальный бюджет",
        "input": {
            "age": 19,
            "skin_type": "oily",
            "concerns": ["acne", "sebum"],
            "budget": "minimum",
            "excluded_ingredients": [],
            "custom_restrictions": [],
            "experience": "guided",
            "values": ["price", "simple_routine"],
            "anonymous_id": "customer-export-04",
        },
    },
    {
        "id": "normal_pigmentation_dullness",
        "title": "Нормальная кожа, пигментация и тусклость",
        "input": {
            "age": 34,
            "skin_type": "normal",
            "concerns": ["pigmentation", "dullness"],
            "budget": "balanced",
            "excluded_ingredients": [],
            "custom_restrictions": [],
            "experience": "guided",
            "values": ["quality"],
            "anonymous_id": "customer-export-05",
        },
    },
    {
        "id": "beginner_simple_no_essential_oils",
        "title": "Новичок, простая рутина, без эфирных масел",
        "input": {
            "age": 22,
            "skin_type": "combination",
            "concerns": ["dryness", "reactivity"],
            "budget": "balanced",
            "excluded_ingredients": ["essential_oils"],
            "custom_restrictions": [],
            "experience": "beginner",
            "values": ["simple_routine", "comfort"],
            "anonymous_id": "customer-export-06",
        },
    },
    {
        "id": "mature_age_changes_premium",
        "title": "Возрастные изменения, премиум-бюджет",
        "input": {
            "age": 42,
            "skin_type": "normal",
            "concerns": ["age_changes", "dryness"],
            "budget": "premium",
            "excluded_ingredients": [],
            "custom_restrictions": [],
            "experience": "guided",
            "values": ["quality", "comfort"],
            "anonymous_id": "customer-export-07",
        },
    },
    {
        "id": "combination_pores_no_alcohol",
        "title": "Комбинированная кожа, поры и себум, без спирта",
        "input": {
            "age": 26,
            "skin_type": "combination",
            "concerns": ["pores", "sebum"],
            "budget": "balanced",
            "excluded_ingredients": ["alcohol"],
            "custom_restrictions": [],
            "experience": "guided",
            "values": ["comfort", "price_quality"],
            "anonymous_id": "customer-export-08",
        },
    },
]


STEP_LABELS = {
    "cleanser": "очищение",
    "toner": "тонер",
    "serum": "сыворотка",
    "moisturizer": "крем",
    "spf": "SPF",
    "exfoliation": "эксфолиация",
    "mask": "маска",
    "treatment": "активный уход",
}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple | set):
        return list(value)
    return [value]


def _product_id(product: dict[str, Any]) -> str:
    return str(product.get("external_id") or product.get("product_id") or "").strip()


def _safe_product(product: dict[str, Any]) -> dict[str, Any]:
    return {
        "external_id": product.get("external_id"),
        "name": product.get("name"),
        "brand": product.get("brand"),
        "routine_step": product.get("routine_step"),
        "category": product.get("category"),
        "price_rub": product.get("price_rub"),
        "budget_segment": product.get("budget_segment"),
        "skin_types": product.get("skin_types") or [],
        "concerns": product.get("concerns") or [],
        "ingredients": product.get("ingredients") or [],
        "key_ingredients": product.get("key_ingredients") or [],
        "ingredient_highlights": product.get("ingredient_highlights"),
        "functional_category": product.get("functional_category"),
        "risk_flags": product.get("risk_flags") or [],
        "ingredient_flags": product.get("ingredient_flags") or [],
        "texture": product.get("texture") or product.get("format"),
        "product_url": product.get("product_url"),
        "image_url": product.get("image_url"),
        "source": product.get("source"),
        "is_active": product.get("is_active"),
        "dataset_verified": product.get("dataset_verified") is True,
        "dataset_external_id": product.get("dataset_external_id") or product.get("external_id"),
    }


def _enrich_product_from_dataset(
    product: dict[str, Any],
    dataset_by_external_id: dict[str, dict[str, Any]] | None,
) -> dict[str, Any]:
    product_id = _product_id(product)
    dataset_product = (dataset_by_external_id or {}).get(product_id)

    if not dataset_product:
        return {
            **product,
            "dataset_verified": False,
            "dataset_external_id": product_id or None,
        }

    return {
        **product,
        **dataset_product,
        "source": "dataset",
        "dataset_verified": True,
        "dataset_external_id": dataset_product.get("external_id") or product_id,
    }


def _ingredients_for_llm(product: dict[str, Any]) -> str:
    key_ingredients = [
        str(item)
        for item in _as_list(product.get("key_ingredients"))
        if str(item).strip()
    ]
    if key_ingredients:
        return ", ".join(key_ingredients[:8])
    ingredients = [str(item) for item in _as_list(product.get("ingredients")) if str(item).strip()]
    return ", ".join(ingredients[:8])


def _matched_concerns(
    item: dict[str, Any],
    product: dict[str, Any],
    scenario_input: dict[str, Any],
) -> list[str]:
    explicit = item.get("matched_concerns")
    if isinstance(explicit, list) and explicit:
        return [str(value) for value in explicit]

    product_concerns = {str(value) for value in _as_list(product.get("concerns"))}
    user_concerns = [str(value) for value in _as_list(scenario_input.get("concerns"))]
    return [concern for concern in user_concerns if concern in product_concerns]


def _llm_context(
    *,
    scenario_input: dict[str, Any],
    product: dict[str, Any],
    step: str,
    matched_concerns: list[str],
    concern_match: int,
) -> dict[str, Any]:
    return {
        "skin_type": scenario_input.get("skin_type"),
        "concerns": scenario_input.get("concerns") or [],
        "matched_concerns": matched_concerns,
        "name": product.get("name"),
        "brand": product.get("brand"),
        "step": STEP_LABELS.get(step, step),
        "ingredients": _ingredients_for_llm(product),
        "concern_match": concern_match,
    }


def _convert_routine_part(
    *,
    part: str,
    items: list[dict[str, Any]],
    scenario_input: dict[str, Any],
    dataset_by_external_id: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    result = []

    for item in items:
        api_product = item.get("product") or {}
        product = _enrich_product_from_dataset(api_product, dataset_by_external_id)
        step = item.get("routine_step") or item.get("step") or product.get("routine_step")
        matched = _matched_concerns(item, product, scenario_input)
        concern_match = len(matched)

        result.append(
            {
                "part": part,
                "step": step,
                "step_label": STEP_LABELS.get(step, step),
                "score": item.get("score"),
                "score_breakdown": item.get("score_breakdown"),
                "matched_concerns": matched,
                "concern_match": concern_match,
                "why_here": item.get("why_here"),
                "product": _safe_product(product),
                "llm_user_prompt_context": _llm_context(
                    scenario_input=scenario_input,
                    product=product,
                    step=str(step or ""),
                    matched_concerns=matched,
                    concern_match=concern_match,
                ),
            }
        )

    return result


def _routine_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    routine = payload.get("routine") or {}
    return [
        *(routine.get("morning") or []),
        *(routine.get("evening") or []),
    ]


def _unique_cosmetic_bag_products(
    routine: dict[str, Any],
    dataset_by_external_id: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    result = []
    seen_ids = set()

    for part in ("morning", "evening"):
        for item in routine.get(part, []) or []:
            api_product = item.get("product") or {}
            product = _enrich_product_from_dataset(api_product, dataset_by_external_id)
            product_id = _product_id(product)

            if not product_id or product_id in seen_ids:
                continue

            seen_ids.add(product_id)
            result.append(_safe_product(product))

    return result


def _quality_issues(
    payload: dict[str, Any],
    dataset_by_external_id: dict[str, dict[str, Any]] | None = None,
) -> list[str]:
    issues = []
    all_items = _routine_items(payload)

    if not all_items:
        issues.append("empty_routine")

    for item in all_items:
        api_product = item.get("product") or {}
        product_id = _product_id(api_product)
        brand = api_product.get("brand")

        if not product_id:
            issues.append("missing_product_external_id")
            continue

        if brand in SAMPLE_BRANDS:
            issues.append(f"sample_brand_returned:{brand}:{product_id}")

        if dataset_by_external_id is not None and product_id not in dataset_by_external_id:
            issues.append(f"not_in_dataset:{product_id}")

    return sorted(set(issues))


def _quality_warnings(payload: dict[str, Any]) -> list[str]:
    warnings = []
    seen_schedule_ids = set()

    for item in _routine_items(payload):
        product = item.get("product") or {}
        product_id = _product_id(product)

        if not product_id:
            continue

        if product_id in seen_schedule_ids:
            warnings.append(f"product_reused_in_schedule:{product_id}")

        seen_schedule_ids.add(product_id)

    return sorted(set(warnings))


async def _load_dataset_products() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    settings = get_settings()
    client: AsyncMongoClient[Any] = AsyncMongoClient(
        settings.mongo_uri,
        uuidRepresentation="standard",
    )

    try:
        await client.admin.command("ping")
        db = client[settings.mongo_db_name]
        products = db["products"]

        total_count = await products.count_documents({})
        dataset_count = await products.count_documents({"source": "dataset"})
        active_dataset_count = await products.count_documents(
            {"source": "dataset", "is_active": True}
        )
        sample_like_count = await products.count_documents(SAMPLE_PRODUCTS_QUERY)

        cursor = products.find({"source": "dataset"}, DATASET_PRODUCT_FIELDS)
        dataset_by_external_id: dict[str, dict[str, Any]] = {}

        async for product in cursor:
            product_id = _product_id(product)
            if product_id:
                dataset_by_external_id[product_id] = product

        report = {
            "database": settings.mongo_db_name,
            "products_total": int(total_count),
            "dataset_products": int(dataset_count),
            "active_dataset_products": int(active_dataset_count),
            "sample_like_products": int(sample_like_count),
            "dataset_products_loaded_for_export": len(dataset_by_external_id),
        }

        return report, dataset_by_external_id
    finally:
        await client.close()


async def _request_recommendation(
    client: httpx.AsyncClient,
    scenario: dict[str, Any],
    dataset_by_external_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    response = await client.post(
        f"{API_BASE_URL}/recommendations",
        json=scenario["input"],
    )

    response.raise_for_status()
    payload = response.json()

    routine = payload.get("routine") or {}
    quality_issues = _quality_issues(payload, dataset_by_external_id)
    quality_warnings = _quality_warnings(payload)

    unique_products = _unique_cosmetic_bag_products(routine, dataset_by_external_id)
    dataset_product_ids = [
        str(product.get("external_id"))
        for product in unique_products
        if product.get("external_id")
    ]

    return {
        "scenario_id": scenario["id"],
        "title": scenario["title"],
        "input": scenario["input"],
        "recommendation_id": payload.get("recommendation_id"),
        "algorithm_version": payload.get("algorithm_version"),
        "skin_profile": payload.get("skin_profile"),
        "filter_summary": payload.get("filter_summary"),
        "total_price_rub": payload.get("total_price_rub"),
        "quality_issues": quality_issues,
        "quality_warnings": quality_warnings,
        "dataset_product_ids": dataset_product_ids,
        "cosmetic_bag_unique_products": unique_products,
        "routine": {
            "morning": _convert_routine_part(
                part="morning",
                items=routine.get("morning") or [],
                scenario_input=scenario["input"],
                dataset_by_external_id=dataset_by_external_id,
            ),
            "evening": _convert_routine_part(
                part="evening",
                items=routine.get("evening") or [],
                scenario_input=scenario["input"],
                dataset_by_external_id=dataset_by_external_id,
            ),
        },
    }


async def build_export() -> dict[str, Any]:
    dataset_report, dataset_by_external_id = await _load_dataset_products()

    result = {
        "export_schema_version": "1.1",
        "generated_at": datetime.now(UTC).isoformat(),
        "purpose": "KOYASH customer review export for LLM prompt verification",
        "api_base_url": API_BASE_URL,
        "important_note": (
            "Product choice is deterministic. LLM must only rewrite explanations "
            "using llm_user_prompt_context. Every exported product is verified "
            "against MongoDB products.source=dataset."
        ),
        "algorithm_contract": {
            "product_selection": "deterministic_backend",
            "llm_role": "explanation_rewrite_only",
            "llm_must_not_add_products_or_medical_claims": True,
        },
        "dataset_provenance": {
            **dataset_report,
            "required_product_source": "dataset",
            "all_export_products_verified_dataset": False,
        },
        "samples": [],
    }

    if dataset_report["dataset_products"] > 0:
        async with httpx.AsyncClient(timeout=30.0) as client:
            for scenario in SCENARIOS:
                result["samples"].append(
                    await _request_recommendation(client, scenario, dataset_by_external_id)
                )

    issue_count = sum(len(sample["quality_issues"]) for sample in result["samples"])
    warning_count = sum(len(sample.get("quality_warnings", [])) for sample in result["samples"])
    unique_bag_count = len(
        {
            tuple(sorted(sample.get("dataset_product_ids") or []))
            for sample in result["samples"]
        }
    )
    exported_product_ids = sorted(
        {
            product_id
            for sample in result["samples"]
            for product_id in sample.get("dataset_product_ids", [])
        }
    )
    all_verified = (
        issue_count == 0
        and dataset_report["dataset_products"] > 0
        and dataset_report["sample_like_products"] == 0
        and all(product_id in dataset_by_external_id for product_id in exported_product_ids)
    )

    result["dataset_provenance"]["exported_dataset_product_count"] = len(exported_product_ids)
    result["dataset_provenance"]["exported_dataset_product_ids"] = exported_product_ids
    result["dataset_provenance"]["all_export_products_verified_dataset"] = all_verified

    result["summary"] = {
        "sample_count": len(result["samples"]),
        "quality_issue_count": issue_count,
        "quality_warning_count": warning_count,
        "unique_cosmetic_bag_count": unique_bag_count,
        "all_products_verified_dataset": all_verified,
        "export_ok": issue_count == 0 and all_verified,
    }

    return result


async def async_main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Export KOYASH customer cosmetic bag samples as UTF-8 JSON.",
    )
    parser.add_argument(
        "--output",
        help=(
            "Optional output path. Use this inside Docker and copy the file with "
            "docker cp to avoid PowerShell encoding issues."
        ),
    )
    args = parser.parse_args(argv)

    result = await build_export()
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
        print(f"Export written to {output_path}", file=sys.stderr)
    else:
        print(rendered, end="")

    if result["summary"]["export_ok"] is not True:
        sys.exit(1)


def main(argv: list[str] | None = None) -> None:
    asyncio.run(async_main(argv))


if __name__ == "__main__":
    main()
