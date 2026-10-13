from typing import Any

from pymongo import ASCENDING, ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase


def _clean_document(document: dict[str, Any]) -> dict[str, Any]:
    document.pop("_id", None)
    return document


class ProductRepository:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.collection = database["products"]

    async def list_active_products(
        self,
        routine_step: str | None = None,
        budget_segment: str | None = None,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {"is_active": True}

        if routine_step:
            query["routine_step"] = routine_step

        if budget_segment:
            query["budget_segment"] = budget_segment

        cursor = self.collection.find(query).sort(
            [("routine_step", ASCENDING), ("price_rub", ASCENDING), ("external_id", ASCENDING)]
        )

        return [_clean_document(document) async for document in cursor]

    async def find_by_external_id(self, external_id: str) -> dict[str, Any] | None:
        document = await self.collection.find_one({"external_id": external_id, "is_active": True})
        if document is None:
            return None
        return _clean_document(document)

    async def find_by_external_ids(
        self,
        external_ids: list[str],
    ) -> dict[str, dict[str, Any]]:
        if not external_ids:
            return {}
        cursor = self.collection.find(
            {
                "external_id": {"$in": list(dict.fromkeys(external_ids))},
                "is_active": True,
            }
        )
        products: dict[str, dict[str, Any]] = {}
        async for document in cursor:
            cleaned = _clean_document(document)
            products[str(cleaned["external_id"])] = cleaned
        return products

    async def list_all_products(self) -> list[dict[str, Any]]:
        cursor = self.collection.find({}).sort("external_id", ASCENDING)
        return [_clean_document(document) async for document in cursor]

    async def find_any_by_external_id(self, external_id: str) -> dict[str, Any] | None:
        document = await self.collection.find_one({"external_id": external_id})
        if document is None:
            return None
        return _clean_document(document)

    async def update_admin_fields(
        self,
        external_id: str,
        changes: dict[str, Any],
    ) -> dict[str, Any] | None:
        document = await self.collection.find_one_and_update(
            {"external_id": external_id},
            {"$set": changes},
            return_document=ReturnDocument.AFTER,
        )
        if document is None:
            return None
        return _clean_document(document)
