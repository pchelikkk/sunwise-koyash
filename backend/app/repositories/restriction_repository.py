from typing import Any

from pymongo import DESCENDING
from pymongo.asynchronous.database import AsyncDatabase

from app.core.time import utc_now


def _clean_document(document: dict[str, Any]) -> dict[str, Any]:
    document.pop("_id", None)
    return document


class RestrictionRepository:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.suggestions = database["restriction_suggestions"]
        self.aliases = database["ingredient_aliases"]
        self.custom_events = database["custom_restriction_events"]

    async def list_popular_suggestions(self, limit: int = 8) -> list[dict[str, Any]]:
        cursor = (
            self.suggestions.find(
                {
                    "status": "approved",
                    "is_popular": True,
                }
            )
            .sort("usage_count", DESCENDING)
            .limit(limit)
        )

        return [_clean_document(document) async for document in cursor]

    async def find_alias(self, raw_value: str) -> dict[str, Any] | None:
        normalized = raw_value.strip().lower()
        document = await self.aliases.find_one(
            {
                "aliases": normalized,
                "is_active": True,
            }
        )
        if document is None:
            return None
        return _clean_document(document)

    async def record_custom_restriction(
        self,
        raw_value: str,
        normalized_key: str,
        anonymous_id: str | None = None,
        user_id: str | None = None,
    ) -> None:
        await self.custom_events.insert_one(
            {
                "raw_value": raw_value,
                "normalized_key": normalized_key,
                "anonymous_id": anonymous_id,
                "user_id": user_id,
                "created_at": utc_now(),
            }
        )

    async def upsert_suggestion_usage(
        self,
        canonical_key: str,
        display_name: str,
        status: str,
        is_popular: bool,
    ) -> None:
        await self.suggestions.update_one(
            {"canonical_key": canonical_key},
            {
                "$set": {
                    "display_name": display_name,
                    "last_used_at": utc_now(),
                },
                "$setOnInsert": {
                    "canonical_key": canonical_key,
                    "status": status,
                    "is_popular": is_popular,
                    "source": "user" if status == "pending" else "system",
                    "created_at": utc_now(),
                },
                "$inc": {"usage_count": 1},
            },
            upsert=True,
        )
