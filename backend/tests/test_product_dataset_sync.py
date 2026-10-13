from pathlib import Path
from uuid import uuid4

import pytest
from pymongo import AsyncMongoClient

from app.core.config import get_settings
from app.importers.product_dataset_sync import sync_product_dataset

DATASET_PATH = Path(__file__).resolve().parents[2] / "data" / "products.xlsx"


@pytest.mark.asyncio
async def test_dataset_sync_is_complete_and_idempotent() -> None:
    settings = get_settings()
    database_name = f"koyash_dataset_sync_test_{uuid4().hex}"
    client = AsyncMongoClient(settings.mongo_uri, uuidRepresentation="standard")
    database = client[database_name]

    try:
        first = await sync_product_dataset(database, DATASET_PATH)
        second = await sync_product_dataset(database, DATASET_PATH)
        products = database["products"]

        assert first["status"] == "synchronized"
        assert first["products"] == 69
        assert second["status"] == "current"
        assert await products.count_documents({"source": "dataset"}) == 69
        assert await products.count_documents({"how_to_use": ""}) == 0
        assert await products.count_documents(
            {
                "product_url": {
                    "$nin": [None, ""],
                    "$not": {"$regex": "^https?://"},
                }
            }
        ) == 0

        await products.delete_one({"source": "dataset"})
        repaired = await sync_product_dataset(database, DATASET_PATH)
        assert repaired["status"] == "synchronized"
        assert await products.count_documents({"source": "dataset"}) == 69

        await database["catalog_import_state"].update_one(
            {"_id": "canonical-product-dataset"},
            {"$set": {"source": "admin_upload", "fingerprint": "admin-file"}},
        )
        await products.delete_one({"source": "dataset"})
        admin_managed = await sync_product_dataset(database, DATASET_PATH)

        assert admin_managed == {
            "status": "admin_managed",
            "fingerprint": "admin-file",
            "products": 68,
        }
        assert await products.count_documents({"source": "dataset"}) == 68
    finally:
        await client.drop_database(database_name)
        await client.close()
