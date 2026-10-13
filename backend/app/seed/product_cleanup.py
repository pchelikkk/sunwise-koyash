from typing import Any

SAMPLE_PRODUCTS_QUERY: dict[str, Any] = {
    "$or": [
        {"source": {"$ne": "dataset"}},
        {"source": None},
        {"source": {"$exists": False}},
        {
            "brand": {
                "$in": [
                    "Koyash Sample",
                    "Soft Lab",
                    "Clear Skin",
                    "Sun Basic",
                    "KOYASH Test",
                ]
            }
        },
        {
            "external_id": {
                "$regex": (
                    "sample|cleanser_00|serum_00|moisturizer_00|spf_00|"
                    "cleanser_001|cleanser_002|serum_001|moisturizer_001|spf_001"
                ),
                "$options": "i",
            }
        },
        {"source": "sample"},
        {"source": "test"},
    ]
}


async def cleanup_demo_products_when_dataset_exists(database: Any) -> dict[str, int]:
    products = database["products"]

    dataset_count = await products.count_documents({"source": "dataset"})

    if dataset_count <= 0:
        return {
            "dataset_products": 0,
            "deleted_demo_products": 0,
        }

    result = await products.delete_many(SAMPLE_PRODUCTS_QUERY)

    return {
        "dataset_products": int(dataset_count),
        "deleted_demo_products": int(result.deleted_count or 0),
    }
