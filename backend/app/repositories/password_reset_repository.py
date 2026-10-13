from datetime import datetime
from typing import Any

from pymongo import ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase

from app.core.time import utc_now


def _clean(document: dict[str, Any]) -> dict[str, Any]:
    document["reset_id"] = str(document.pop("_id"))
    return document


class PasswordResetRepository:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.collection = database["password_reset_tokens"]

    async def create_token(
        self,
        user_id: str,
        email: str,
        token_hash: str,
        expires_at: datetime,
    ) -> dict[str, Any]:
        now = utc_now()

        document = {
            "user_id": user_id,
            "email": email.lower(),
            "token_hash": token_hash,
            "expires_at": expires_at,
            "used_at": None,
            "created_at": now,
        }

        result = await self.collection.insert_one(document)
        document["_id"] = result.inserted_id

        return _clean(document)

    async def consume_valid_by_hash(self, token_hash: str) -> dict[str, Any] | None:
        document = await self.collection.find_one_and_update(
            {
                "token_hash": token_hash,
                "used_at": None,
                "expires_at": {"$gt": utc_now()},
            },
            {"$set": {"used_at": utc_now()}},
            return_document=ReturnDocument.AFTER,
        )

        if document is None:
            return None

        return _clean(document)

    async def invalidate_user_tokens(self, user_id: str) -> None:
        await self.collection.update_many(
            {"user_id": user_id, "used_at": None},
            {"$set": {"used_at": utc_now()}},
        )
