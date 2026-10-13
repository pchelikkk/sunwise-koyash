from pathlib import Path

ROOT = Path(r"C:\Projects\sunwise-koyash")


def write_file(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")


write_file("backend/tests/test_replacement_filter_contract.py", """
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
""")


write_file("backend/scripts/backend_consistency_audit.py", """
import asyncio
import json
import os
from pathlib import Path
from typing import Any

from pymongo import AsyncMongoClient

from app.core.config import get_settings
from app.main import app


IMPORTANT_COLLECTIONS = [
    "products",
    "ingredient_aliases",
    "restriction_suggestions",
    "recommendation_sessions",
    "feedback_events",
    "replacement_sessions",
    "analytics_events",
    "analytics_daily_metrics",
    "llm_explanation_logs",
    "users",
    "user_profiles",
    "password_reset_tokens",
]


SAMPLE_MARKERS = [
    "sample",
    "koyash sample",
    "soft lab",
    "clear skin",
    "sun basic",
]


def _route_list() -> list[dict[str, Any]]:
    routes = []

    for route in app.routes:
        path = getattr(route, "path", "")
        methods = sorted(getattr(route, "methods", []) or [])

        if path.startswith("/api"):
            routes.append(
                {
                    "path": path,
                    "methods": methods,
                    "name": getattr(route, "name", None),
                }
            )

    return sorted(routes, key=lambda item: (item["path"], ",".join(item["methods"])))


def _dataset_files() -> list[str]:
    roots = [
        Path("/app/../data"),
        Path("/app/data"),
        Path("/app"),
    ]

    files: list[str] = []

    for root in roots:
        if not root.exists():
            continue

        for pattern in ("*.xlsx", "*.csv"):
            for path in root.rglob(pattern):
                if "node_modules" not in path.parts and ".git" not in path.parts:
                    files.append(str(path))

    return sorted(set(files))


async def _db_report() -> dict[str, Any]:
    mongo_uri = os.environ.get("MONGO_URI")
    db_name = os.environ.get("MONGO_DB_NAME", "koyash")

    if not mongo_uri:
        return {
            "status": "skipped",
            "reason": "MONGO_URI is not configured",
        }

    client: AsyncMongoClient[Any] = AsyncMongoClient(mongo_uri, uuidRepresentation="standard")

    try:
        await client.admin.command("ping")
        db = client[db_name]
        existing = set(await db.list_collection_names())

        counts = {}
        for name in IMPORTANT_COLLECTIONS:
            counts[name] = await db[name].count_documents({}) if name in existing else 0

        sample_count = 0
        if "products" in existing:
            sample_query = {
                "$or": [
                    {
                        "external_id": {
                            "$regex": "sample|cleanser_00|serum_00|moisturizer_00|spf_00",
                            "$options": "i",
                        }
                    },
                    {"name": {"$regex": "|".join(SAMPLE_MARKERS), "$options": "i"}},
                    {"brand": {"$regex": "|".join(SAMPLE_MARKERS), "$options": "i"}},
                ]
            }
            sample_count = await db["products"].count_documents(sample_query)

        return {
            "status": "ok",
            "database": db_name,
            "counts": counts,
            "sample_like_products": sample_count,
        }
    finally:
        await client.close()


async def main() -> None:
    settings = get_settings()

    report = {
        "service": settings.app_name,
        "environment": settings.app_env,
        "api_prefix": settings.api_v1_prefix,
        "routes": _route_list(),
        "settings_presence": {
            "jwt_secret_key": hasattr(settings, "jwt_secret_key"),
            "analytics_raw_event_ttl_days": hasattr(settings, "analytics_raw_event_ttl_days"),
            "llm_enabled": hasattr(settings, "llm_enabled"),
            "vsellm_model": hasattr(settings, "vsellm_model"),
            "password_reset_token_expire_minutes": hasattr(
                settings,
                "password_reset_token_expire_minutes",
            ),
            "smtp_enabled": hasattr(settings, "smtp_enabled"),
            "frontend_base_url": hasattr(settings, "frontend_base_url"),
        },
        "llm": {
            "enabled": getattr(settings, "llm_enabled", False),
            "provider": getattr(settings, "llm_provider", "vsellm"),
            "model": getattr(settings, "vsellm_model", None),
            "api_key_configured": bool(getattr(settings, "vsellm_api_key", None)),
        },
        "smtp": {
            "enabled": getattr(settings, "smtp_enabled", False),
            "host_configured": bool(getattr(settings, "smtp_host", None)),
            "from_email": getattr(settings, "smtp_from_email", None),
        },
        "db": await _db_report(),
        "dataset_files": _dataset_files(),
        "notes": [
            "LLM does not choose products. Deterministic filters and scoring remain the source of truth.",
            "Real product import is intentionally not included in Step 4.3.",
            "Sample products are acceptable before Step 4.4, but must be isolated before product demo.",
        ],
    }

    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
""")


old_script = ROOT / "scripts" / "apply_step_41_password_reset.py"
if old_script.exists():
    old_script.unlink()

print("Step 4.3 part 1 files written successfully.")