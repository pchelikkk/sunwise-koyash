from typing import Any

from bson import ObjectId
from pymongo import DESCENDING
from pymongo.asynchronous.database import AsyncDatabase

from app.core.time import utc_now


def _json_safe(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)

    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items() if key != "_id"}

    if isinstance(value, list):
        return [_json_safe(item) for item in value]

    return value


def _clean(document: dict[str, Any]) -> dict[str, Any]:
    document["replacement_session_id"] = str(document.pop("_id"))
    return _json_safe(document)


class ReplacementRepository:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.collection = database["replacement_sessions"]

    async def create(
        self,
        *,
        recommendation_id: str,
        feedback_id: str,
        original_product_external_id: str,
        reason: str,
        candidates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        now = utc_now()

        document = {
            "recommendation_id": recommendation_id,
            "feedback_id": feedback_id,
            "original_product_external_id": original_product_external_id,
            "reason": reason,
            "replacement_candidates": _json_safe(candidates),
            "selected_product_external_id": None,
            "created_at": now,
            "updated_at": now,
        }

        result = await self.collection.insert_one(document)
        document["_id"] = result.inserted_id

        return _clean(document)

    async def list_by_recommendation(
        self,
        recommendation_id: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        cursor = (
            self.collection.find({"recommendation_id": recommendation_id})
            .sort("created_at", DESCENDING)
            .limit(limit)
        )

        documents = await cursor.to_list(length=limit)
        return [_clean(document) for document in documents]

    async def find_by_id(
        self,
        session_id: str,
    ) -> dict[str, Any] | None:
        if not ObjectId.is_valid(session_id):
            return None

        document = await self.collection.find_one({"_id": ObjectId(session_id)})

        if document is None:
            return None

        return _clean(document)

    async def select(
        self,
        *,
        session_id: str,
        product_external_id: str,
    ) -> dict[str, Any] | None:
        if not ObjectId.is_valid(session_id):
            return None

        result = await self.collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "selected_product_external_id": product_external_id,
                    "updated_at": utc_now(),
                }
            },
        )

        if result.matched_count != 1:
            return None

        return await self.find_by_id(session_id)
