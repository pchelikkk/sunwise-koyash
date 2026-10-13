import json
import os
from typing import Any

import httpx
from pymongo import MongoClient

API_BASE_URL = os.environ.get("KOYASH_API_BASE_URL", "http://127.0.0.1:8000/api/v1")

SAMPLE_BRANDS = {
    "Koyash Sample",
    "Soft Lab",
    "Clear Skin",
    "Sun Basic",
}

SCENARIOS = [
    {
        "id": "combination_acne_sebum_no_fragrance",
        "label": "Комбинированная кожа, высыпания и жирный блеск, без отдушек",
        "body": {
            "age": 24,
            "skin_type": "combination",
            "concerns": ["acne", "sebum"],
            "budget": "balanced",
            "excluded_ingredients": ["fragrance"],
            "custom_restrictions": [],
            "experience": "guided",
            "values": ["comfort", "price_quality"],
            "anonymous_id": "audit-combination-acne-sebum",
        },
        "forbidden": ["fragrance"],
    },
    {
        "id": "sensitive_reactivity_no_fragrance_no_alcohol",
        "label": "Чувствительная кожа, реактивность, без отдушек и спирта",
        "body": {
            "age": 27,
            "skin_type": "sensitive",
            "concerns": ["reactivity", "redness"],
            "budget": "balanced",
            "excluded_ingredients": ["fragrance", "alcohol"],
            "custom_restrictions": [],
            "experience": "guided",
            "values": ["comfort", "soft_formula"],
            "anonymous_id": "audit-sensitive-reactivity",
        },
        "forbidden": ["fragrance", "alcohol"],
    },
    {
        "id": "dry_dehydration_budget_minimum",
        "label": "Сухость/обезвоженность, минимальный бюджет",
        "body": {
            "age": 31,
            "skin_type": "dry",
            "concerns": ["dryness", "dehydration"],
            "budget": "minimum",
            "excluded_ingredients": [],
            "custom_restrictions": [],
            "experience": "guided",
            "values": ["price", "comfort"],
            "anonymous_id": "audit-dry-budget",
        },
        "forbidden": [],
    },
    {
        "id": "oily_sebum_acne_budget_minimum",
        "label": "Жирная кожа, себум и высыпания, минимальный бюджет",
        "body": {
            "age": 19,
            "skin_type": "oily",
            "concerns": ["sebum", "acne"],
            "budget": "minimum",
            "excluded_ingredients": [],
            "custom_restrictions": [],
            "experience": "guided",
            "values": ["price", "simple_routine"],
            "anonymous_id": "audit-oily-minimum",
        },
        "forbidden": [],
    },
    {
        "id": "pigmentation_spf_focus",
        "label": "Пигментация, нужен SPF/осветление",
        "body": {
            "age": 34,
            "skin_type": "normal",
            "concerns": ["pigmentation", "dullness"],
            "budget": "balanced",
            "excluded_ingredients": [],
            "custom_restrictions": [],
            "experience": "guided",
            "values": ["quality"],
            "anonymous_id": "audit-pigmentation",
        },
        "forbidden": [],
    },
    {
        "id": "beginner_simple_routine_no_essential_oils",
        "label": "Новичок, простая рутина, без эфирных масел",
        "body": {
            "age": 22,
            "skin_type": "combination",
            "concerns": ["dryness", "reactivity"],
            "budget": "balanced",
            "excluded_ingredients": ["essential_oils"],
            "custom_restrictions": [],
            "experience": "beginner",
            "values": ["simple_routine", "comfort"],
            "anonymous_id": "audit-beginner-simple",
        },
        "forbidden": ["essential_oils"],
    },
]


FORBIDDEN_MARKERS = {
    "fragrance": [
        "contains_fragrance",
        "fragrance",
        "parfum",
        "perfume",
        "отдушка",
        "отдушки",
    ],
    "alcohol": [
        "contains_alcohol",
        "drying_alcohol",
        "alcohol denat",
        "denatured alcohol",
        "sd alcohol",
        "ethanol",
        "ethyl alcohol",
        "этанол",
        "денатурированный спирт",
    ],
    "essential_oils": [
        "contains_essential_oils",
        "essential oil",
        "essential oils",
        "эфирное масло",
        "эфирные масла",
        "bergamot",
        "tea tree",
        "patchouli",
    ],
}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, tuple | set):
        return list(value)

    return [value]


def _product_text(product: dict[str, Any]) -> str:
    fields = [
        "ingredients",
        "key_ingredients",
        "ingredient_highlights",
        "ingredient_flags",
        "risk_flags",
        "allergens",
        "issues",
        "description",
        "functional_category",
    ]

    values = []

    for field in fields:
        raw = product.get(field)

        if isinstance(raw, list):
            values.extend(str(item) for item in raw)
        elif raw is not None:
            values.append(str(raw))

    return " | ".join(values).lower()


def _product_has_forbidden(product: dict[str, Any], restriction: str) -> bool:
    markers = FORBIDDEN_MARKERS.get(restriction, [])
    text = _product_text(product)

    return any(marker.lower() in text for marker in markers)


def _routine_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    routine = payload.get("routine", {})
    result = []

    for part in ("morning", "evening"):
        for item in routine.get(part, []) or []:
            product = item.get("product", {})
            result.append(
                {
                    "part": part,
                    "routine_step": item.get("routine_step") or product.get("routine_step"),
                    "score": item.get("score"),
                    "why_here": item.get("why_here"),
                    "product": {
                        "external_id": product.get("external_id"),
                        "brand": product.get("brand"),
                        "name": product.get("name"),
                        "price_rub": product.get("price_rub"),
                        "routine_step": product.get("routine_step"),
                        "budget_segment": product.get("budget_segment"),
                        "skin_types": product.get("skin_types"),
                        "concerns": product.get("concerns"),
                        "risk_flags": product.get("risk_flags"),
                    },
                }
            )

    return result


def _db_report() -> dict[str, Any]:
    mongo_uri = os.environ["MONGO_URI"]
    db_name = os.environ.get("MONGO_DB_NAME", "koyash")

    db = MongoClient(mongo_uri)[db_name]

    sample_query = {
        "$or": [
            {"source": "sample"},
            {"brand": {"$in": list(SAMPLE_BRANDS)}},
            {
                "external_id": {
                    "$regex": "sample|cleanser_00|serum_00|moisturizer_00|spf_00",
                    "$options": "i",
                }
            },
        ]
    }

    step_counts = list(
        db.products.aggregate(
            [
                {"$group": {"_id": "$routine_step", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
            ]
        )
    )

    risk_counts = list(
        db.products.aggregate(
            [
                {"$unwind": {"path": "$risk_flags", "preserveNullAndEmptyArrays": False}},
                {"$group": {"_id": "$risk_flags", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 20},
            ]
        )
    )

    source_counts = list(
        db.products.aggregate(
            [
                {"$group": {"_id": "$source", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
            ]
        )
    )

    return {
        "products_total": db.products.count_documents({}),
        "dataset_products": db.products.count_documents({"source": "dataset"}),
        "sample_like_products": db.products.count_documents(sample_query),
        "source_counts": source_counts,
        "routine_step_counts": step_counts,
        "risk_flag_counts": risk_counts,
    }


def _run_scenario(client: httpx.Client, scenario: dict[str, Any]) -> dict[str, Any]:
    response = client.post(
        f"{API_BASE_URL}/recommendations",
        json=scenario["body"],
    )

    item: dict[str, Any] = {
        "id": scenario["id"],
        "label": scenario["label"],
        "status_code": response.status_code,
        "issues": [],
    }

    if response.status_code != 200:
        item["issues"].append(f"HTTP {response.status_code}")
        item["raw_response"] = response.text[:1000]
        return item

    payload = response.json()
    routine_items = _routine_items(payload)
    filter_summary = payload.get("filter_summary", {})

    item["filter_summary"] = filter_summary
    item["total_price_rub"] = payload.get("total_price_rub")
    item["routine_count"] = len(routine_items)
    item["routine"] = routine_items

    if not routine_items:
        item["issues"].append("empty_routine")

    allowed_products = filter_summary.get("allowed_products")
    total_products = filter_summary.get("total_products")

    if isinstance(allowed_products, int) and allowed_products == 0:
        item["issues"].append("zero_allowed_products")

    if isinstance(total_products, int) and total_products == 0:
        item["issues"].append("zero_total_products")

    for routine_item in routine_items:
        product = routine_item["product"]
        brand = product.get("brand")

        if brand in SAMPLE_BRANDS:
            item["issues"].append(f"sample_brand_returned:{brand}")

        for restriction in scenario.get("forbidden", []):
            if _product_has_forbidden(product, restriction):
                item["issues"].append(
                    f"forbidden_{restriction}_returned:{product.get('external_id')}"
                )

    return item


def main() -> None:
    report: dict[str, Any] = {
        "api_base_url": API_BASE_URL,
        "db": _db_report(),
        "scenarios": [],
    }

    with httpx.Client(timeout=30.0) as client:
        for scenario in SCENARIOS:
            report["scenarios"].append(_run_scenario(client, scenario))

    issue_count = sum(len(item["issues"]) for item in report["scenarios"])
    empty_routine_count = sum(
        1 for item in report["scenarios"] if "empty_routine" in item["issues"]
    )

    report["summary"] = {
        "scenario_count": len(report["scenarios"]),
        "issue_count": issue_count,
        "empty_routine_count": empty_routine_count,
        "audit_passed": issue_count == 0,
    }

    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))

    if issue_count == 0:
        print("AUDIT RESULT: OK")
    else:
        print("AUDIT RESULT: ATTENTION")


if __name__ == "__main__":
    main()
