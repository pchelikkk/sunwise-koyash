from typing import Any

from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase

from app.core.time import utc_now


def _clean(document: dict[str, Any]) -> dict[str, Any]:
    document["feedback_id"] = str(document.pop("_id"))
    return document


class FeedbackRepository:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.collection = database["feedback_events"]

    async def create(
        self,
        *,
        recommendation_id: str,
        product_external_id: str,
        reason: str,
        comment: str | None,
        anonymous_id: str | None,
    ) -> dict[str, Any]:
        now = utc_now()

        document = {
            "recommendation_id": recommendation_id,
            "product_external_id": product_external_id,
            "reason": reason,
            "comment": comment,
            "anonymous_id": anonymous_id,
            "created_at": now,
        }

        result = await self.collection.insert_one(document)
        document["_id"] = result.inserted_id

        return _clean(document)

    async def find_by_id(self, feedback_id: str) -> dict[str, Any] | None:
        if not ObjectId.is_valid(feedback_id):
            return None

        document = await self.collection.find_one({"_id": ObjectId(feedback_id)})

        if document is None:
            return None

        return _clean(document)
