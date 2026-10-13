import argparse
import asyncio
import json
import sys
from typing import Any

from pymongo import AsyncMongoClient

from app.core.config import get_settings
from app.seed.product_cleanup import SAMPLE_PRODUCTS_QUERY


async def async_main(strict_dataset: bool) -> None:
    settings = get_settings()
    client: AsyncMongoClient[Any] = AsyncMongoClient(
        settings.mongo_uri,
        uuidRepresentation="standard",
    )

    try:
        await client.admin.command("ping")
        products = client[settings.mongo_db_name]["products"]

        total = await products.count_documents({})
        dataset = await products.count_documents(
            {"source": "dataset"}
        )
        non_dataset = await products.count_documents(
            {"source": {"$ne": "dataset"}}
        )
        sample_like = await products.count_documents(
            SAMPLE_PRODUCTS_QUERY
        )

        strict_dataset_ok = (
            total > 0
            and total == dataset
            and non_dataset == 0
            and sample_like == 0
        )

        report = {
            "database": settings.mongo_db_name,
            "total": int(total),
            "dataset": int(dataset),
            "non_dataset": int(non_dataset),
            "sample_like": int(sample_like),
            "strict_dataset_ok": strict_dataset_ok,
        }

        print(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2,
            )
        )

        if strict_dataset and not strict_dataset_ok:
            sys.exit(1)
    finally:
        await client.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--strict-dataset",
        action="store_true",
    )
    args = parser.parse_args()

    asyncio.run(
        async_main(args.strict_dataset)
    )


if __name__ == "__main__":
    main()
