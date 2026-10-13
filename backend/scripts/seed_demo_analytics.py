import argparse
import asyncio
import random
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.core.security import create_password_hash
from app.core.time import utc_now
from app.db.mongodb import close_mongo_connection, connect_to_mongo, get_database

SEED_VERSION = "presentation-v3"
SEED_FIELD = "demo_seed_version"


def weighted_choice(rng: random.Random, values: list[str], weights: list[int]) -> str:
    return rng.choices(values, weights=weights, k=1)[0]


async def clean_legacy_demo(database: Any) -> dict[str, int]:
    test_user_documents = [
        item
        async for item in database["users"].find(
            {"email": {"$regex": "@example\\.com$", "$options": "i"}},
            {"_id": 1},
        )
    ]
    user_object_ids = [item["_id"] for item in test_user_documents]
    user_ids = [str(value) for value in user_object_ids]
    sample_product = {"$regex": "^(cleanser|toner|serum|treatment|moisturizer|spf)_"}
    recommendation_query = {
        "$or": [
            {"user_id": {"$in": user_ids}},
            {"result.routine.morning.product.external_id": sample_product},
            {"result.routine.evening.product.external_id": sample_product},
        ]
    }
    legacy_recommendations = database["recommendation_sessions"].find(
        recommendation_query,
        {"recommendation_id": 1},
    )
    recommendation_ids = [
        str(item["recommendation_id"])
        async for item in legacy_recommendations
        if item.get("recommendation_id")
    ]

    deleted_profiles = await database["user_profiles"].delete_many(
        {"user_id": {"$in": user_ids}}
    )
    deleted_favorites = await database["product_favorites"].delete_many(
        {"user_id": {"$in": user_ids}}
    )
    deleted_bag_items = await database["cosmetic_bag_items"].delete_many(
        {"user_id": {"$in": user_ids}}
    )
    deleted_users = await database["users"].delete_many(
        {"_id": {"$in": user_object_ids}}
    )
    deleted_events = await database["analytics_events"].delete_many(
        {
            "$or": [
                {"user_id": {"$in": user_ids}},
                {"recommendation_id": {"$in": recommendation_ids}},
                {"product_external_id": sample_product},
                {"metadata.source": {"$in": ["test", "demo_script"]}},
            ]
        }
    )
    deleted_feedback = await database["feedback_events"].delete_many(
        {
            "$or": [
                {"user_id": {"$in": user_ids}},
                {"recommendation_id": {"$in": recommendation_ids}},
                {"product_external_id": sample_product},
            ]
        }
    )
    deleted_replacements = await database["replacement_sessions"].delete_many(
        {
            "$or": [
                {"recommendation_id": {"$in": recommendation_ids}},
                {"original_product_external_id": sample_product},
                {"selected_product_external_id": sample_product},
            ]
        }
    )
    deleted_recommendations = await database["recommendation_sessions"].delete_many(
        recommendation_query
    )
    return {
        "users": deleted_users.deleted_count,
        "profiles": deleted_profiles.deleted_count,
        "favorites": deleted_favorites.deleted_count,
        "cosmetic_bag_items": deleted_bag_items.deleted_count,
        "events": deleted_events.deleted_count,
        "recommendations": deleted_recommendations.deleted_count,
        "feedback": deleted_feedback.deleted_count,
        "replacements": deleted_replacements.deleted_count,
    }


async def main(*, clean_legacy: bool = False) -> None:
    if get_settings().is_production:
        raise RuntimeError("Demo analytics seeding is disabled in production")
    await connect_to_mongo()
    database = get_database()
    rng = random.Random(260716)
    now = utc_now()

    cleanup_result = await clean_legacy_demo(database) if clean_legacy else None

    product_cursor = (
        database["products"]
        .find({"is_active": {"$ne": False}}, {"_id": 0, "external_id": 1})
        .sort("external_id", 1)
        .limit(12)
    )
    product_ids = [
        str(item["external_id"])
        async for item in product_cursor
        if item.get("external_id")
    ]
    if len(product_ids) < 6:
        raise RuntimeError("Seed requires at least six active catalog products")

    collections = (
        "users",
        "analytics_events",
        "recommendation_sessions",
        "feedback_events",
        "replacement_sessions",
    )
    for collection_name in collections:
        await database[collection_name].delete_many({SEED_FIELD: SEED_VERSION})

    disabled_password_hash = create_password_hash(f"disabled-{uuid4().hex}")
    user_documents = []
    for index in range(72):
        created_days_ago = rng.randint(3, 120)
        last_seen_days_ago = rng.randint(0, min(created_days_ago, 42))
        created_at = now - timedelta(days=created_days_ago, hours=rng.randint(0, 20))
        last_seen_at = now - timedelta(days=last_seen_days_ago, hours=rng.randint(0, 20))
        user_documents.append(
            {
                "email": f"demo.analytics+{index:03d}@koyash.local",
                "password_hash": disabled_password_hash,
                "full_name": "Демо-пользователь",
                "role": "user",
                "is_active": True,
                "auth_version": 0,
                "created_at": created_at,
                "updated_at": last_seen_at,
                "last_seen_at": last_seen_at,
                SEED_FIELD: SEED_VERSION,
            }
        )
    user_result = await database["users"].insert_many(user_documents)
    user_ids = [str(value) for value in user_result.inserted_ids]

    skin_types = ["combination", "oily", "dry", "sensitive", "normal"]
    concerns = ["acne", "sebum", "dryness", "sensitivity", "pigmentation", "texture"]
    budgets = ["minimum", "balanced", "premium"]
    experiences = ["beginner", "guided", "advanced"]
    feedback_reasons = [
        "too_expensive",
        "texture_not_suitable",
        "composition_concern",
        "dislikes_brand",
        "too_many_steps",
        "other",
    ]

    recommendation_documents = []
    analytics_documents = []
    recommendation_contexts = []
    for index in range(210):
        created_at = now - timedelta(
            days=rng.randint(0, 89),
            hours=rng.randint(0, 23),
            minutes=rng.randint(0, 59),
        )
        registered = rng.random() < 0.72
        user_id = rng.choice(user_ids) if registered else None
        anonymous_id = None if registered else f"demo-guest-{rng.randint(1, 55):03d}"
        skin_type = weighted_choice(rng, skin_types, [37, 23, 18, 14, 8])
        primary_concern = weighted_choice(
            rng,
            concerns,
            [30, 21, 20, 14, 9, 6],
        )
        selected_concerns = [primary_concern]
        if rng.random() < 0.58:
            secondary = rng.choice([item for item in concerns if item != primary_concern])
            selected_concerns.append(secondary)
        budget = weighted_choice(rng, budgets, [31, 55, 14])
        experience = weighted_choice(rng, experiences, [46, 38, 16])

        featured = [product_ids[0], product_ids[1], product_ids[2], product_ids[3]]
        morning_ids = [featured[0], featured[1], featured[3]]
        evening_ids = [featured[0], featured[1], featured[2]]
        if rng.random() < 0.35:
            morning_ids[-1] = rng.choice(product_ids[4:])
        if rng.random() < 0.42:
            evening_ids[-1] = rng.choice(product_ids[4:])

        recommendation_id = f"demo-rec-{index:04d}-{uuid4().hex[:8]}"
        recommendation_documents.append(
            {
                "recommendation_id": recommendation_id,
                "user_id": user_id,
                "anonymous_id": anonymous_id,
                "request": {
                    "skin_type": skin_type,
                    "concerns": selected_concerns,
                    "budget": budget,
                    "experience": experience,
                    "excluded_ingredients": (
                        ["fragrance"] if skin_type == "sensitive" else []
                    ),
                    "custom_restrictions": [],
                },
                "result": {
                    "routine": {
                        "morning": [
                            {"product": {"external_id": product_id}}
                            for product_id in morning_ids
                        ],
                        "evening": [
                            {"product": {"external_id": product_id}}
                            for product_id in evening_ids
                        ],
                    }
                },
                "created_at": created_at,
                SEED_FIELD: SEED_VERSION,
            }
        )
        recommendation_contexts.append(
            {
                "recommendation_id": recommendation_id,
                "created_at": created_at,
                "user_id": user_id,
                "anonymous_id": anonymous_id,
                "product_ids": list(dict.fromkeys([*morning_ids, *evening_ids])),
            }
        )

        actor = {"user_id": user_id, "anonymous_id": anonymous_id}
        analytics_documents.extend(
            [
                {
                    "event_type": "questionnaire_completed",
                    "event_source": "server",
                    **actor,
                    "recommendation_id": recommendation_id,
                    "metadata": {"source": "presentation_seed"},
                    "created_at": created_at,
                    SEED_FIELD: SEED_VERSION,
                },
                {
                    "event_type": (
                        "llm_explanation_fallback" if index % 19 == 0 else "llm_explanation_success"
                    ),
                    "event_source": "server",
                    **actor,
                    "recommendation_id": recommendation_id,
                    "metadata": {
                        "provider": "openai",
                        "model": "presentation-model",
                        "source": "presentation_seed",
                    },
                    "created_at": created_at + timedelta(seconds=2),
                    SEED_FIELD: SEED_VERSION,
                },
                {
                    "event_type": "result_viewed",
                    "event_source": "public",
                    **actor,
                    "recommendation_id": recommendation_id,
                    "metadata": {"source": "presentation_seed"},
                    "created_at": created_at + timedelta(minutes=1),
                    SEED_FIELD: SEED_VERSION,
                },
            ]
        )
        if rng.random() < 0.22:
            analytics_documents.append(
                {
                    "event_type": "recommendation_shared",
                    "event_source": "public",
                    **actor,
                    "recommendation_id": recommendation_id,
                    "metadata": {"source": "presentation_seed"},
                    "created_at": created_at + timedelta(minutes=5),
                    SEED_FIELD: SEED_VERSION,
                }
            )
        for product_index, product_id in enumerate(recommendation_contexts[-1]["product_ids"][:3]):
            if rng.random() < (0.82 - product_index * 0.16):
                analytics_documents.append(
                    {
                        "event_type": "product_details_opened",
                        "event_source": "public",
                        **actor,
                        "recommendation_id": recommendation_id,
                        "product_external_id": product_id,
                        "metadata": {"source": "presentation_seed"},
                        "created_at": created_at + timedelta(minutes=2 + product_index),
                        SEED_FIELD: SEED_VERSION,
                    }
                )
            if rng.random() < (0.33 - product_index * 0.07):
                analytics_documents.append(
                    {
                        "event_type": "favorite_added",
                        "event_source": "public",
                        **actor,
                        "recommendation_id": recommendation_id,
                        "product_external_id": product_id,
                        "metadata": {"source": "presentation_seed"},
                        "created_at": created_at + timedelta(minutes=6 + product_index),
                        SEED_FIELD: SEED_VERSION,
                    }
                )
            if rng.random() < (0.25 - product_index * 0.05):
                analytics_documents.append(
                    {
                        "event_type": "cosmetic_bag_added",
                        "event_source": "public",
                        **actor,
                        "recommendation_id": recommendation_id,
                        "product_external_id": product_id,
                        "metadata": {"source": "presentation_seed"},
                        "created_at": created_at + timedelta(minutes=9 + product_index),
                        SEED_FIELD: SEED_VERSION,
                    }
                )
            if rng.random() < (0.18 - product_index * 0.04):
                analytics_documents.append(
                    {
                        "event_type": "store_opened",
                        "event_source": "public",
                        **actor,
                        "recommendation_id": recommendation_id,
                        "product_external_id": product_id,
                        "metadata": {"source": "presentation_seed"},
                        "created_at": created_at + timedelta(minutes=12 + product_index),
                        SEED_FIELD: SEED_VERSION,
                    }
                )

    await database["recommendation_sessions"].insert_many(recommendation_documents)
    await database["analytics_events"].insert_many(analytics_documents)

    feedback_documents = []
    replacement_documents = []
    for index, context in enumerate(rng.sample(recommendation_contexts, 74)):
        original_id = context["product_ids"][index % min(3, len(context["product_ids"]))]
        reason = weighted_choice(rng, feedback_reasons, [36, 21, 17, 12, 8, 6])
        feedback_id = f"demo-feedback-{index:03d}-{uuid4().hex[:8]}"
        feedback_time = context["created_at"] + timedelta(minutes=12)
        feedback_documents.append(
            {
                "feedback_id": feedback_id,
                "recommendation_id": context["recommendation_id"],
                "product_external_id": original_id,
                "reason": reason,
                "comment": None,
                "user_id": context["user_id"],
                "anonymous_id": context["anonymous_id"],
                "created_at": feedback_time,
                SEED_FIELD: SEED_VERSION,
            }
        )
        if index < 58:
            alternatives = [item for item in product_ids if item != original_id]
            selected_id = rng.choice(alternatives[:5]) if rng.random() < 0.78 else None
            replacement_documents.append(
                {
                    "replacement_session_id": f"demo-replacement-{index:03d}",
                    "recommendation_id": context["recommendation_id"],
                    "feedback_id": feedback_id,
                    "original_product_external_id": original_id,
                    "selected_product_external_id": selected_id,
                    "reason": reason,
                    "created_at": feedback_time + timedelta(seconds=2),
                    "updated_at": feedback_time + timedelta(minutes=2),
                    SEED_FIELD: SEED_VERSION,
                }
            )

    await database["feedback_events"].insert_many(feedback_documents)
    await database["replacement_sessions"].insert_many(replacement_documents)

    print(
        "DEMO ANALYTICS SEED OK",
        {
            "legacy_cleanup": cleanup_result,
            "users": len(user_documents),
            "recommendations": len(recommendation_documents),
            "events": len(analytics_documents),
            "feedback": len(feedback_documents),
            "replacements": len(replacement_documents),
        },
    )
    await close_mongo_connection()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed presentation-safe KOYASH analytics")
    parser.add_argument(
        "--clean-legacy-demo",
        action="store_true",
        help="Remove known local test accounts and legacy sample-product analytics",
    )
    args = parser.parse_args()
    asyncio.run(main(clean_legacy=args.clean_legacy_demo))
