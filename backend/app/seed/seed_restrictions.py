from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.core.time import utc_now

RESTRICTIONS = [
    {
        "canonical_key": "fragrance",
        "display_name": "Отдушки",
        "usage_count": 64,
        "source": "system",
        "status": "approved",
        "is_popular": True,
    },
    {
        "canonical_key": "alcohol",
        "display_name": "Спирт",
        "usage_count": 51,
        "source": "system",
        "status": "approved",
        "is_popular": True,
    },
    {
        "canonical_key": "essential_oils",
        "display_name": "Эфирные масла",
        "usage_count": 38,
        "source": "system",
        "status": "approved",
        "is_popular": True,
    },
    {
        "canonical_key": "none",
        "display_name": "Нет ограничений",
        "usage_count": 32,
        "source": "system",
        "status": "approved",
        "is_popular": True,
    },
    {
        "canonical_key": "unknown",
        "display_name": "Затрудняюсь ответить",
        "usage_count": 20,
        "source": "system",
        "status": "approved",
        "is_popular": True,
    },
]


async def seed_restrictions(database: AsyncDatabase[Any]) -> None:
    collection = database["restriction_suggestions"]

    for restriction in RESTRICTIONS:
        await collection.update_one(
            {"canonical_key": restriction["canonical_key"]},
            {
                "$set": {
                    **restriction,
                    "updated_at": utc_now(),
                },
                "$setOnInsert": {
                    "created_at": utc_now(),
                },
            },
            upsert=True,
        )
