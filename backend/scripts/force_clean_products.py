import asyncio
import json
from typing import Any

from pymongo import AsyncMongoClient

from app.core.config import get_settings
from app.seed.product_cleanup import SAMPLE_PRODUCTS_QUERY


async def main() -> None:
    settings = get_settings()
    client: AsyncMongoClient[Any] = AsyncMongoClient(
        settings.mongo_uri,
        uuidRepresentation="standard",
    )

    try:
        db = client[settings.mongo_db_name]
        products = db["products"]

        before = {
            "total": await products.count_documents({}),
            "dataset": await products.count_documents({"source": "dataset"}),
            "sample_like": await products.count_documents(SAMPLE_PRODUCTS_QUERY),
        }

        result = await products.delete_many(SAMPLE_PRODUCTS_QUERY)

        after = {
            "total": await products.count_documents({}),
            "dataset": await products.count_documents({"source": "dataset"}),
            "sample_like": await products.count_documents(SAMPLE_PRODUCTS_QUERY),
        }

        print(
            json.dumps(
                {
                    "before": before,
                    "deleted_count": int(result.deleted_count or 0),
                    "after": after,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
