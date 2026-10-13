from typing import Any

from pymongo import ASCENDING, DESCENDING
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import OperationFailure


async def _create_index_safely(
    collection: Any,
    keys: Any,
    **kwargs: Any,
) -> None:
    try:
        await collection.create_index(keys, **kwargs)
    except OperationFailure as exc:
        if getattr(exc, "code", None) == 86:
            return
        raise


async def create_indexes(database: AsyncDatabase, analytics_ttl_days: int) -> None:
    ttl_seconds = analytics_ttl_days * 24 * 60 * 60

    await _create_index_safely(database["users"], "email", unique=True)
    await _create_index_safely(database["users"], "role")
    await _create_index_safely(database["users"], "created_at")
    await _create_index_safely(database["user_profiles"], "user_id", unique=True)
    await _create_index_safely(
        database["product_favorites"],
        [("user_id", ASCENDING), ("product_external_id", ASCENDING)],
        unique=True,
    )
    await _create_index_safely(
        database["product_favorites"],
        [("user_id", ASCENDING), ("created_at", DESCENDING)],
    )
    await _create_index_safely(
        database["cosmetic_bag_items"],
        [("user_id", ASCENDING), ("product_external_id", ASCENDING)],
        unique=True,
    )
    await _create_index_safely(
        database["cosmetic_bag_items"],
        [("user_id", ASCENDING), ("created_at", DESCENDING)],
    )

    await _create_index_safely(database["products"], "external_id", unique=True)
    await _create_index_safely(
        database["products"], [("is_active", ASCENDING), ("routine_step", ASCENDING)]
    )
    await _create_index_safely(
        database["products"], [("category", ASCENDING), ("budget_segment", ASCENDING)]
    )

    await _create_index_safely(database["ingredient_aliases"], "canonical_key", unique=True)
    await _create_index_safely(database["restriction_suggestions"], "canonical_key", unique=True)
    await _create_index_safely(
        database["restriction_suggestions"],
        [("status", ASCENDING), ("usage_count", DESCENDING)],
    )

    await _create_index_safely(database["custom_restriction_events"], "normalized_key")
    await _create_index_safely(database["custom_restriction_events"], "created_at")

    await _create_index_safely(database["recommendation_sessions"], "user_id")
    await _create_index_safely(database["recommendation_sessions"], "anonymous_id")
    await _create_index_safely(database["recommendation_sessions"], "created_at")

    await _create_index_safely(database["feedback_events"], "recommendation_id")
    await _create_index_safely(database["feedback_events"], "product_external_id")
    await _create_index_safely(database["feedback_events"], "reason")
    await _create_index_safely(database["feedback_events"], "created_at")
    await _create_index_safely(
        database["feedback_events"],
        [("reason", ASCENDING), ("created_at", DESCENDING)],
    )

    await _create_index_safely(database["replacement_sessions"], "recommendation_id")
    await _create_index_safely(database["replacement_sessions"], "feedback_id")
    await _create_index_safely(database["replacement_sessions"], "created_at")
    await _create_index_safely(database["replacement_sessions"], "selected_product_external_id")

    await _create_index_safely(database["analytics_events"], "event_type")
    await _create_index_safely(database["analytics_events"], "event_source")
    await _create_index_safely(database["analytics_events"], "recommendation_id")
    await _create_index_safely(database["analytics_events"], "product_external_id")
    await _create_index_safely(
        database["analytics_events"], "created_at", expireAfterSeconds=ttl_seconds
    )
    await _create_index_safely(
        database["analytics_events"],
        [("event_type", ASCENDING), ("created_at", DESCENDING)],
    )
    await _create_index_safely(
        database["analytics_events"],
        [("event_source", ASCENDING), ("event_type", ASCENDING), ("created_at", DESCENDING)],
    )
    await _create_index_safely(database["analytics_events"], "anonymous_id")
    await _create_index_safely(database["analytics_events"], "user_id")

    await _create_index_safely(
        database["analytics_daily_metrics"],
        [("date", ASCENDING), ("metric", ASCENDING)],
    )

    await _create_index_safely(database["llm_explanation_logs"], "recommendation_id")
    await _create_index_safely(database["llm_explanation_logs"], "created_at")

    await _create_index_safely(database["password_reset_tokens"], "token_hash", unique=True)
    await _create_index_safely(database["password_reset_tokens"], "user_id")
    await _create_index_safely(
        database["password_reset_tokens"], "expires_at", expireAfterSeconds=0
    )
    await _create_index_safely(database["password_reset_tokens"], "used_at")

    await _create_index_safely(
        database["admin_audit_events"],
        [("created_at", DESCENDING), ("admin_user_id", ASCENDING)],
    )
    await _create_index_safely(
        database["admin_audit_events"],
        [("product_external_id", ASCENDING), ("created_at", DESCENDING)],
    )
