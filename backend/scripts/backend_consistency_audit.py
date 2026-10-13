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
    "product_favorites",
    "cosmetic_bag_items",
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
    routes: list[dict[str, Any]] = []
    allowed_methods = {"delete", "get", "head", "options", "patch", "post", "put"}

    for path, operations in app.openapi().get("paths", {}).items():
        if not path.startswith("/api"):
            continue
        methods = sorted(
            method.upper()
            for method in operations
            if method.lower() in allowed_methods
        )
        operation_ids = sorted(
            str(operation.get("operationId"))
            for method, operation in operations.items()
            if method.lower() in allowed_methods and operation.get("operationId")
        )
        routes.append(
            {
                "path": path,
                "methods": methods,
                "name": ",".join(operation_ids) or None,
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
    llm_provider = str(getattr(settings, "llm_provider", "openai")).lower()
    if llm_provider == "openai":
        llm_model = getattr(settings, "openai_model", None)
        llm_key_configured = bool(getattr(settings, "openai_api_key", None))
    else:
        llm_model = getattr(settings, "vsellm_model", None)
        llm_key_configured = bool(getattr(settings, "vsellm_api_key", None))

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
            "provider": llm_provider,
            "model": llm_model,
            "api_key_configured": llm_key_configured,
        },
        "smtp": {
            "enabled": getattr(settings, "smtp_enabled", False),
            "host_configured": bool(getattr(settings, "smtp_host", None)),
            "from_email": getattr(settings, "smtp_from_email", None),
        },
        "db": await _db_report(),
        "dataset_files": _dataset_files(),
        "notes": [
            "LLM does not choose products. Deterministic filters and scoring "
            "remain the source of truth.",
            "Real product import is intentionally not included in Step 4.3.",
            "Sample products are acceptable before Step 4.4, but must be "
            "isolated before product demo.",
        ],
    }

    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
