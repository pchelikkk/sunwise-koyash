from pathlib import Path

ROOT = Path(r"C:\Projects\sunwise-koyash")


def write_file(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")


write_file("backend/scripts/export_customer_cosmetic_bags.py", r'''
import argparse
import asyncio
import json
import os
import sys
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
    key_ingredients = [str(item) for item in _as_list(product.get("key_ingredients")) if str(item).strip()]
    if key_ingredients:
        return ", ".join(key_ingredients[:8])
    ingredients = [str(item) for item in _as_list(product.get("ingredients")) if str(item).strip()]
    return ", ".join(ingredients[:8])


def _matched_concerns(item: dict[str, Any], product: dict[str, Any], scenario_input: dict[str, Any]) -> list[str]:
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
    concern_match: int,
) -> dict[str, Any]:
    return {
        "skin_type": scenario_input.get("skin_type"),
        "concerns": scenario_input.get("concerns") or [],
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
        "purpose": "KOYASH customer review export for LLM prompt tuning",
        "api_base_url": API_BASE_URL,
        "important_note": (
            "Product choice is deterministic. LLM must only rewrite explanations "
            "using llm_user_prompt_context. Every exported product is verified "
            "against MongoDB products.source=dataset."
        ),
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
''')


write_file("backend/scripts/validate_customer_cosmetic_bags.py", r'''
import argparse
import json
import sys
from pathlib import Path
from typing import Any


SAMPLE_BRANDS = {
    "Koyash Sample",
    "Soft Lab",
    "Clear Skin",
    "Sun Basic",
    "KOYASH Test",
}

MOJIBAKE_MARKERS = ("╨", "╤", "Ð", "Ñ", "â")


def _walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]

    if isinstance(value, dict):
        result: list[str] = []
        for key, item in value.items():
            result.extend(_walk_strings(key))
            result.extend(_walk_strings(item))
        return result

    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(_walk_strings(item))
        return result

    return []


def _routine_items(sample: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    routine = sample.get("routine") or {}
    result: list[tuple[str, dict[str, Any]]] = []

    for part in ("morning", "evening"):
        for item in routine.get(part) or []:
            result.append((part, item))

    return result


def _item_step(item: dict[str, Any]) -> str:
    product = item.get("product") or {}
    return str(item.get("step") or item.get("routine_step") or product.get("routine_step") or "")


def _unique_product_ids(sample: dict[str, Any]) -> tuple[str, ...]:
    products = sample.get("cosmetic_bag_unique_products") or []
    ids = [str(product.get("external_id")) for product in products if product.get("external_id")]

    if not ids:
        for _, item in _routine_items(sample):
            product = item.get("product") or {}
            product_id = product.get("external_id")
            if product_id:
                ids.append(str(product_id))

    return tuple(sorted(set(ids)))


def _validate_export_product(
    *,
    errors: list[str],
    scenario_id: str,
    product: dict[str, Any],
    location: str,
) -> None:
    product_id = product.get("external_id") or "unknown"
    brand = product.get("brand")
    source = product.get("source")
    dataset_verified = product.get("dataset_verified")
    dataset_external_id = product.get("dataset_external_id")

    if brand in SAMPLE_BRANDS:
        errors.append(f"{scenario_id}:{location}:sample_brand:{brand}:{product_id}")

    if source != "dataset":
        errors.append(f"{scenario_id}:{location}:source_is_not_dataset:{source}:{product_id}")

    if dataset_verified is not True:
        errors.append(f"{scenario_id}:{location}:dataset_verified_is_not_true:{product_id}")

    if dataset_external_id != product_id:
        errors.append(
            f"{scenario_id}:{location}:dataset_external_id_mismatch:{dataset_external_id}:{product_id}"
        )

    if not product.get("name") or not product.get("brand"):
        errors.append(f"{scenario_id}:{location}:missing_product_identity:{product_id}")

    if not product.get("routine_step"):
        errors.append(f"{scenario_id}:{location}:missing_routine_step:{product_id}")


def validate_export(path: str | Path) -> dict[str, Any]:
    export_path = Path(path)
    raw_text = export_path.read_text(encoding="utf-8-sig")
    data = json.loads(raw_text)

    errors: list[str] = []
    warnings: list[str] = []

    if any(marker in raw_text for marker in MOJIBAKE_MARKERS):
        errors.append("mojibake_detected")

    summary = data.get("summary") or {}
    provenance = data.get("dataset_provenance") or {}
    samples = data.get("samples") or []

    if summary.get("sample_count") != 8:
        errors.append(f"expected_8_samples_got_{summary.get('sample_count')}")

    if len(samples) != 8:
        errors.append(f"expected_8_sample_items_got_{len(samples)}")

    if summary.get("quality_issue_count") != 0:
        errors.append(f"quality_issue_count_not_zero:{summary.get('quality_issue_count')}")

    if summary.get("export_ok") is not True:
        errors.append("summary_export_ok_is_not_true")

    if summary.get("all_products_verified_dataset") is not True:
        errors.append("summary_all_products_verified_dataset_is_not_true")

    if provenance.get("required_product_source") != "dataset":
        errors.append("dataset_provenance_required_product_source_is_not_dataset")

    if provenance.get("all_export_products_verified_dataset") is not True:
        errors.append("dataset_provenance_all_export_products_verified_dataset_is_not_true")

    if int(provenance.get("dataset_products") or 0) <= 0:
        errors.append("dataset_provenance_has_no_dataset_products")

    if int(provenance.get("sample_like_products") or 0) != 0:
        errors.append(f"dataset_provenance_sample_like_not_zero:{provenance.get('sample_like_products')}")

    strings = _walk_strings(data)
    bad_strings = [text for text in strings if any(marker in text for marker in MOJIBAKE_MARKERS)]

    if bad_strings:
        errors.append(f"mojibake_strings:{len(bad_strings)}")

    unique_bags = set()

    for sample in samples:
        scenario_id = sample.get("scenario_id", "unknown")
        sample_issues = sample.get("quality_issues") or []

        if sample_issues:
            errors.append(f"{scenario_id}:quality_issues:{sample_issues}")

        product_ids = _unique_product_ids(sample)

        if not product_ids:
            errors.append(f"{scenario_id}:empty_cosmetic_bag")
        else:
            unique_bags.add(product_ids)

        for index, product in enumerate(sample.get("cosmetic_bag_unique_products") or []):
            _validate_export_product(
                errors=errors,
                scenario_id=scenario_id,
                product=product,
                location=f"unique_products[{index}]",
            )

        for part, item in _routine_items(sample):
            step = _item_step(item)
            product = item.get("product") or {}
            product_id = product.get("external_id") or "unknown"

            _validate_export_product(
                errors=errors,
                scenario_id=scenario_id,
                product=product,
                location=f"routine.{part}",
            )

            if step == "spf" and part != "morning":
                errors.append(f"{scenario_id}:spf_not_morning:{product_id}")

            if step == "exfoliation" and part == "morning":
                errors.append(f"{scenario_id}:exfoliation_in_morning:{product_id}")

            llm_context = item.get("llm_user_prompt_context") or {}
            if not llm_context.get("name") or not llm_context.get("step"):
                warnings.append(f"{scenario_id}:weak_llm_context:{product_id}")

    if len(unique_bags) < 5:
        errors.append(f"expected_at_least_5_unique_cosmetic_bags_got_{len(unique_bags)}")

    return {
        "path": str(export_path),
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
        "dataset_provenance": provenance,
        "unique_cosmetic_bag_count": len(unique_bags),
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Validate KOYASH customer cosmetic bag export JSON.")
    parser.add_argument("path")
    args = parser.parse_args(argv)

    report = validate_export(args.path)
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if not report["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
''')


write_file("backend/tests/test_customer_cosmetic_bags_export.py", r'''
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
''')


write_file("backend/tests/test_customer_cosmetic_bags_validator.py", r'''
import json

from scripts.validate_customer_cosmetic_bags import validate_export


def _product(product_id: str, *, step: str = "cleanser", source: str | None = "dataset", verified: bool = True) -> dict:
    return {
        "external_id": product_id,
        "name": product_id,
        "brand": "Dataset Brand",
        "routine_step": step,
        "source": source,
        "dataset_verified": verified,
        "dataset_external_id": product_id,
    }


def _item(product_id: str, *, step: str = "cleanser", part: str = "morning") -> dict:
    return {
        "part": part,
        "step": step,
        "product": _product(product_id, step=step),
        "llm_user_prompt_context": {
            "name": product_id,
            "step": step,
        },
    }


def _sample(index: int, product_id: str) -> dict:
    return {
        "scenario_id": f"scenario_{index}",
        "title": f"Сценарий {index}",
        "quality_issues": [],
        "quality_warnings": [],
        "dataset_product_ids": [product_id],
        "cosmetic_bag_unique_products": [_product(product_id)],
        "routine": {
            "morning": [_item(product_id, step="cleanser", part="morning")],
            "evening": [],
        },
    }


def _payload(samples: list[dict]) -> dict:
    return {
        "dataset_provenance": {
            "database": "koyash",
            "products_total": 69,
            "dataset_products": 69,
            "sample_like_products": 0,
            "dataset_products_loaded_for_export": 69,
            "required_product_source": "dataset",
            "all_export_products_verified_dataset": True,
            "exported_dataset_product_count": 5,
            "exported_dataset_product_ids": [f"product_{index}" for index in range(5)],
        },
        "summary": {
            "sample_count": 8,
            "quality_issue_count": 0,
            "quality_warning_count": 0,
            "unique_cosmetic_bag_count": 5,
            "all_products_verified_dataset": True,
            "export_ok": True,
        },
        "samples": samples,
    }


def test_validator_accepts_clean_utf8_dataset_verified_export(tmp_path) -> None:
    samples = [_sample(index, f"product_{index % 5}") for index in range(8)]
    path = tmp_path / "export.json"
    path.write_text(json.dumps(_payload(samples), ensure_ascii=False), encoding="utf-8")

    report = validate_export(path)

    assert report["ok"] is True
    assert report["unique_cosmetic_bag_count"] == 5


def test_validator_rejects_mojibake(tmp_path) -> None:
    samples = [_sample(index, f"product_{index % 5}") for index in range(8)]
    samples[0]["title"] = "╨Ъ╨╛╨╝╨▒╨╕"
    path = tmp_path / "export.json"
    path.write_text(json.dumps(_payload(samples), ensure_ascii=False), encoding="utf-8")

    report = validate_export(path)

    assert report["ok"] is False
    assert any("mojibake" in error for error in report["errors"])


def test_validator_rejects_spf_in_evening(tmp_path) -> None:
    samples = [_sample(index, f"product_{index % 5}") for index in range(8)]
    samples[0]["routine"] = {
        "morning": [],
        "evening": [_item("spf_bad", step="spf", part="evening")],
    }
    samples[0]["cosmetic_bag_unique_products"] = [_product("spf_bad", step="spf")]
    samples[0]["dataset_product_ids"] = ["spf_bad"]
    path = tmp_path / "export.json"
    path.write_text(json.dumps(_payload(samples), ensure_ascii=False), encoding="utf-8")

    report = validate_export(path)

    assert report["ok"] is False
    assert any("spf_not_morning" in error for error in report["errors"])


def test_validator_rejects_non_dataset_product_source(tmp_path) -> None:
    samples = [_sample(index, f"product_{index % 5}") for index in range(8)]
    samples[0]["cosmetic_bag_unique_products"][0] = _product(
        "product_0",
        source=None,
        verified=False,
    )
    samples[0]["routine"]["morning"][0]["product"] = _product(
        "product_0",
        source=None,
        verified=False,
    )
    path = tmp_path / "export.json"
    path.write_text(json.dumps(_payload(samples), ensure_ascii=False), encoding="utf-8")

    report = validate_export(path)

    assert report["ok"] is False
    assert any("source_is_not_dataset" in error for error in report["errors"])
    assert any("dataset_verified_is_not_true" in error for error in report["errors"])
''')


print("Step 4.8.1 strict dataset export patch applied successfully.")