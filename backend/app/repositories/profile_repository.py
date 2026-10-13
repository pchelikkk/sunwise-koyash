from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.core.time import utc_now


def _clean_profile(document: dict[str, Any]) -> dict[str, Any]:
    document["profile_id"] = str(document.pop("_id"))
    document.setdefault("age", None)
    document.setdefault("concerns", [])
    document.setdefault("primary_concern", None)
    document.setdefault("sensitivity_level", None)
    document.setdefault("excluded_ingredients", [])
    document.setdefault("custom_restrictions", [])
    document.setdefault("values", [])
    document.setdefault("routine_preference", None)
    document.setdefault("texture_preference", None)
    document.setdefault("questionnaire_history", [])
    document.setdefault("feedback_history", [])
    return document


class ProfileRepository:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.collection = database["user_profiles"]

    async def create_default_profile(
        self,
        user_id: str,
        anonymous_id: str | None = None,
    ) -> dict[str, Any]:
        now = utc_now()

        document = {
            "user_id": user_id,
            "anonymous_id": anonymous_id,
            "age": None,
            "skin_type": None,
            "concerns": [],
            "primary_concern": None,
            "sensitivity_level": None,
            "budget": None,
            "excluded_ingredients": [],
            "custom_restrictions": [],
            "experience": None,
            "routine_preference": None,
            "texture_preference": None,
            "values": [],
            "questionnaire_history": [],
            "feedback_history": [],
            "created_at": now,
            "updated_at": now,
        }

        result = await self.collection.insert_one(document)
        document["_id"] = result.inserted_id

        return _clean_profile(document)

    async def find_by_user_id(self, user_id: str) -> dict[str, Any] | None:
        document = await self.collection.find_one({"user_id": user_id})

        if document is None:
            return None

        return _clean_profile(document)

    async def ensure_profile(
        self,
        user_id: str,
        anonymous_id: str | None = None,
    ) -> dict[str, Any]:
        profile = await self.find_by_user_id(user_id)

        if profile is not None:
            return profile

        return await self.create_default_profile(
            user_id=user_id,
            anonymous_id=anonymous_id,
        )

    async def update_profile(
        self,
        user_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        allowed_fields = {
            "age",
            "skin_type",
            "concerns",
            "primary_concern",
            "sensitivity_level",
            "budget",
            "excluded_ingredients",
            "custom_restrictions",
            "experience",
            "routine_preference",
            "texture_preference",
            "values",
        }

        update = {
            key: value
            for key, value in payload.items()
            if key in allowed_fields and value is not None
        }

        update["updated_at"] = utc_now()

        await self.collection.update_one(
            {"user_id": user_id},
            {"$set": update},
        )

        return await self.find_by_user_id(user_id)

    async def append_questionnaire_history(
        self,
        user_id: str,
        entry: dict[str, Any],
    ) -> dict[str, Any] | None:
        now = utc_now()
        history_entry = {
            **entry,
            "created_at": now,
        }

        await self.collection.update_one(
            {"user_id": user_id},
            {
                "$push": {
                    "questionnaire_history": {
                        "$each": [history_entry],
                        "$slice": -20,
                    }
                },
                "$set": {"updated_at": now},
            },
        )

        return await self.find_by_user_id(user_id)

    async def sync_anonymous_id(
        self,
        user_id: str,
        anonymous_id: str | None,
    ) -> None:
        if anonymous_id is None:
            return

        await self.collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "anonymous_id": anonymous_id,
                    "updated_at": utc_now(),
                }
            },
        )
