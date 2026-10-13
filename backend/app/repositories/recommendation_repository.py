from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import DESCENDING
from pymongo.asynchronous.database import AsyncDatabase

from app.core.time import utc_now


class RecommendationRepository:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.collection = database["recommendation_sessions"]

    async def save_session(
        self,
        request: dict[str, Any],
        result: dict[str, Any],
        algorithm_version: str,
        anonymous_id: str | None = None,
        user_id: str | None = None,
    ) -> str:
        document = {
            "request": request,
            "result": result,
            "algorithm_version": algorithm_version,
            "anonymous_id": anonymous_id,
            "user_id": user_id,
            "created_at": utc_now(),
        }

        insert_result = await self.collection.insert_one(document)
        return str(insert_result.inserted_id)

    async def find_by_id(self, recommendation_id: str) -> dict[str, Any] | None:
        try:
            object_id = ObjectId(recommendation_id)
        except InvalidId:
            return None

        document = await self.collection.find_one({"_id": object_id})
        if document is None:
            return None

        document["recommendation_id"] = str(document.pop("_id"))
        return document

    async def claim_anonymous_sessions(
        self,
        *,
        anonymous_id: str | None,
        user_id: str,
    ) -> int:
        """Attach this browser's guest recommendations to an authenticated user.

        The anonymous id is generated and retained by the browser. Only unowned
        sessions are claimable, so signing in can never move another account's
        recommendation history.
        """

        normalized_anonymous_id = str(anonymous_id or "").strip()
        if not normalized_anonymous_id or not ObjectId.is_valid(user_id):
            return 0

        result = await self.collection.update_many(
            {
                "anonymous_id": normalized_anonymous_id,
                "$or": [
                    {"user_id": None},
                    {"user_id": {"$exists": False}},
                ],
            },
            {
                "$set": {
                    "user_id": user_id,
                    "claimed_at": utc_now(),
                }
            },
        )
        return int(result.modified_count)

    async def replace_routine_product(
        self,
        *,
        recommendation_id: str,
        original_product_external_id: str,
        replacement_item: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Replace an item in every daypart and persist the recalculated total.

        A product may intentionally occur in both the morning and evening
        routines. Both occurrences are replaced so the stored recommendation,
        subsequent history reads, and the frontend always agree.
        """

        try:
            object_id = ObjectId(recommendation_id)
        except InvalidId:
            return None

        document = await self.collection.find_one({"_id": object_id})
        if document is None:
            return None

        result = document.get("result")
        routine = result.get("routine") if isinstance(result, dict) else None
        if not isinstance(routine, dict):
            return None

        replacement_count = 0
        updated_routine: dict[str, list[dict[str, Any]]] = {}
        for daypart in ("morning", "evening"):
            values = routine.get(daypart)
            items = values if isinstance(values, list) else []
            updated_items: list[dict[str, Any]] = []
            for item in items:
                product = item.get("product") if isinstance(item, dict) else None
                external_id = (
                    str(product.get("external_id") or "")
                    if isinstance(product, dict)
                    else ""
                )
                if external_id == original_product_external_id:
                    updated_items.append(replacement_item)
                    replacement_count += 1
                else:
                    updated_items.append(item)
            updated_routine[daypart] = updated_items

        if replacement_count == 0:
            return None

        unique_products: dict[str, dict[str, Any]] = {}
        for item in [
            *updated_routine["morning"],
            *updated_routine["evening"],
        ]:
            product = item.get("product") if isinstance(item, dict) else None
            if not isinstance(product, dict):
                continue
            external_id = str(product.get("external_id") or "")
            if external_id:
                unique_products[external_id] = product

        total_price_rub = sum(
            int(product.get("price_rub") or 0)
            for product in unique_products.values()
        )
        updated_at = utc_now()
        update_result = await self.collection.update_one(
            {
                "_id": object_id,
                "$or": [
                    {
                        "result.routine.morning.product.external_id": (
                            original_product_external_id
                        )
                    },
                    {
                        "result.routine.evening.product.external_id": (
                            original_product_external_id
                        )
                    },
                ],
            },
            {
                "$set": {
                    "result.routine": updated_routine,
                    "result.total_price_rub": total_price_rub,
                    "updated_at": updated_at,
                }
            },
        )
        if update_result.matched_count != 1:
            return None

        return {
            "routine": updated_routine,
            "total_price_rub": total_price_rub,
            "updated_at": updated_at,
        }

    async def list_by_user_id(
        self,
        user_id: str,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        query = {"user_id": user_id}
        total = await self.collection.count_documents(query)
        cursor = (
            self.collection.find(query).sort("created_at", DESCENDING).skip(offset).limit(limit)
        )
        documents: list[dict[str, Any]] = []
        async for document in cursor:
            document["recommendation_id"] = str(document.pop("_id"))
            documents.append(document)
        return documents, total
