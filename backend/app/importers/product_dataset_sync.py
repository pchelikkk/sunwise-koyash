import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.importers.product_dataset import load_products_from_dataset

DATASET_STATE_ID = "canonical-product-dataset"


def _dataset_fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


async def sync_product_dataset(
    database: AsyncDatabase[Any],
    path: str | Path,
) -> dict[str, Any]:
    """Idempotently synchronize the validated canonical dataset into MongoDB."""

    dataset_path = Path(path)
    preview = load_products_from_dataset(dataset_path)
    if preview.errors:
        first_errors = "; ".join(
            f"row {error.row_number}: {error.reason}" for error in preview.errors[:5]
        )
        raise RuntimeError(
            f"Product dataset contains {len(preview.errors)} invalid rows: {first_errors}"
        )

    fingerprint = _dataset_fingerprint(dataset_path)
    products = database["products"]
    state_collection = database["catalog_import_state"]
    state = await state_collection.find_one({"_id": DATASET_STATE_ID})
    dataset_count = await products.count_documents({"source": "dataset"})

    # An administrator-uploaded dataset is the new runtime source of truth. Keep
    # it across container restarts instead of silently restoring the bundled
    # onboarding workbook.
    if state and state.get("source") == "admin_upload":
        return {
            "status": "admin_managed",
            "fingerprint": state.get("fingerprint"),
            "products": dataset_count,
        }

    if (
        state
        and state.get("fingerprint") == fingerprint
        and dataset_count == len(preview.products)
    ):
        return {
            "status": "current",
            "fingerprint": fingerprint,
            "products": dataset_count,
        }

    now = datetime.now(UTC)
    external_ids: list[str] = []

    for product in preview.products:
        external_id = product["external_id"]
        external_ids.append(external_id)
        await products.update_one(
            {"external_id": external_id},
            {
                "$set": {
                    **product,
                    "dataset_fingerprint": fingerprint,
                    "imported_at": now,
                    "updated_at": now,
                },
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )

    await products.delete_many(
        {
            "source": "dataset",
            "external_id": {"$nin": external_ids},
        }
    )
    await state_collection.update_one(
        {"_id": DATASET_STATE_ID},
        {
            "$set": {
                "source": "bundled_dataset",
                "fingerprint": fingerprint,
                "path": str(dataset_path),
                "product_count": len(external_ids),
                "synced_at": now,
            }
        },
        upsert=True,
    )

    return {
        "status": "synchronized",
        "fingerprint": fingerprint,
        "products": len(external_ids),
    }
