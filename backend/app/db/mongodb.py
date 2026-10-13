from typing import Any

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import get_settings
from app.db.indexes import create_indexes


class MongoDB:
    client: AsyncMongoClient[Any] | None = None
    database: AsyncDatabase[Any] | None = None


mongodb = MongoDB()


async def connect_to_mongo() -> None:
    settings = get_settings()

    mongodb.client = AsyncMongoClient(settings.mongo_uri, uuidRepresentation="standard")
    await mongodb.client.admin.command("ping")

    mongodb.database = mongodb.client[settings.mongo_db_name]
    await create_indexes(
        database=mongodb.database,
        analytics_ttl_days=settings.analytics_raw_event_ttl_days,
    )


async def close_mongo_connection() -> None:
    if mongodb.client is not None:
        await mongodb.client.close()
        mongodb.client = None
        mongodb.database = None


def get_database() -> AsyncDatabase[Any]:
    if mongodb.database is None:
        raise RuntimeError("MongoDB is not connected")
    return mongodb.database
