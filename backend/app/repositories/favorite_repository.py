from typing import Any

from pymongo import DESCENDING, ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase

from app.core.time import utc_now


class FavoriteRepository:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.collection = database["product_favorites"]

    async def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        cursor = self.collection.find({"user_id": user_id}).sort(
            "created_at",
            DESCENDING,
        )
        result: list[dict[str, Any]] = []
        async for document in cursor:
            document.pop("_id", None)
            document.pop("user_id", None)
            result.append(document)
        return result

    async def upsert(self, user_id: str, product_external_id: str) -> dict[str, Any]:
        now = utc_now()
        document = await self.collection.find_one_and_update(
            {
                "user_id": user_id,
                "product_external_id": product_external_id,
            },
            {
                "$setOnInsert": {
                    "user_id": user_id,
                    "product_external_id": product_external_id,
                    "created_at": now,
                }
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        if document is None:
            raise RuntimeError("Favorite upsert did not return a document")
        document.pop("_id", None)
        document.pop("user_id", None)
        return document

    async def remove(self, user_id: str, product_external_id: str) -> bool:
        result = await self.collection.delete_one(
            {
                "user_id": user_id,
                "product_external_id": product_external_id,
            }
        )
        return result.deleted_count > 0
