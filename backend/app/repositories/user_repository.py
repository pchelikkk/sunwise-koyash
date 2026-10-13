from typing import Any

from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase

from app.core.enums import UserRole
from app.core.time import utc_now


def _clean_user(document: dict[str, Any], include_password_hash: bool = False) -> dict[str, Any]:
    document["user_id"] = str(document.pop("_id"))
    document.setdefault("role", UserRole.USER.value)
    document.setdefault("auth_version", 0)

    if not include_password_hash:
        document.pop("password_hash", None)

    return document


class UserRepository:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.collection = database["users"]

    async def create_user(
        self,
        email: str,
        password_hash: str,
        full_name: str | None = None,
        anonymous_id: str | None = None,
    ) -> dict[str, Any]:
        now = utc_now()

        document = {
            "email": email.lower(),
            "password_hash": password_hash,
            "full_name": full_name,
            "anonymous_id": anonymous_id,
            "role": UserRole.USER.value,
            "is_active": True,
            "auth_version": 0,
            "created_at": now,
            "updated_at": now,
            "last_seen_at": now,
        }

        result = await self.collection.insert_one(document)
        document["_id"] = result.inserted_id

        return _clean_user(document)

    async def find_by_email(
        self,
        email: str,
        include_password_hash: bool = False,
    ) -> dict[str, Any] | None:
        document = await self.collection.find_one({"email": email.lower()})

        if document is None:
            return None

        return _clean_user(document, include_password_hash=include_password_hash)

    async def find_by_id(
        self,
        user_id: str,
        include_password_hash: bool = False,
    ) -> dict[str, Any] | None:
        if not ObjectId.is_valid(user_id):
            return None

        document = await self.collection.find_one({"_id": ObjectId(user_id)})

        if document is None:
            return None

        return _clean_user(document, include_password_hash=include_password_hash)

    async def update_last_seen(self, user_id: str) -> None:
        if not ObjectId.is_valid(user_id):
            return

        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"last_seen_at": utc_now()}},
        )

    async def update_user(
        self,
        user_id: str,
        full_name: str | None = None,
        anonymous_id: str | None = None,
    ) -> dict[str, Any] | None:
        if not ObjectId.is_valid(user_id):
            return None

        update: dict[str, Any] = {"updated_at": utc_now()}

        if full_name is not None:
            update["full_name"] = full_name

        if anonymous_id is not None:
            update["anonymous_id"] = anonymous_id

        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update},
        )

        return await self.find_by_id(user_id)

    async def update_password(
        self,
        user_id: str,
        password_hash: str,
    ) -> bool:
        if not ObjectId.is_valid(user_id):
            return False

        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "password_hash": password_hash,
                    "updated_at": utc_now(),
                },
                "$inc": {"auth_version": 1},
            },
        )

        return result.modified_count == 1

    async def set_role_by_email(
        self,
        email: str,
        role: UserRole,
    ) -> dict[str, Any] | None:
        result = await self.collection.update_one(
            {"email": email.lower()},
            {
                "$set": {
                    "role": role.value,
                    "updated_at": utc_now(),
                }
            },
        )

        if result.matched_count != 1:
            return None

        return await self.find_by_email(email)
