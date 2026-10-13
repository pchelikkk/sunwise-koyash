import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pymongo import AsyncMongoClient

from app.core.config import get_settings
from app.importers.product_dataset import load_products_from_dataset

SAMPLE_PRODUCTS_QUERY = {
    "$or": [
        {"source": {"$ne": "dataset"}},
        {"source": "sample"},
        {
            "external_id": {
                "$regex": "sample|cleanser_00|serum_00|moisturizer_00|spf_00",
                "$options": "i",
            }
        },
        {
            "brand": {
                "$regex": "Koyash Sample|Soft Lab|Clear Skin|Sun Basic",
                "$options": "i",
            }
        },
    ]
}


def _json_default(value: Any) -> str:
    return str(value)


async def _delete_count(collection, query: dict[str, Any], dry_run: bool) -> int:
    count = await collection.count_documents(query)

    if dry_run:
        return count

    await collection.delete_many(query)
    return count


async def import_products(args: argparse.Namespace) -> dict[str, Any]:
    settings = get_settings()
    client: AsyncMongoClient[Any] = AsyncMongoClient(
        settings.mongo_uri,
        uuidRepresentation="standard",
    )

    try:
        await client.admin.command("ping")
        db = client[settings.mongo_db_name]
        products_collection = db["products"]

        report: dict[str, Any] = {
            "database": settings.mongo_db_name,
            "dry_run": args.dry_run,
            "file": args.file,
            "sample_products_deleted": 0,
            "dataset_products_deleted": 0,
            "rows_valid": 0,
            "rows_invalid": 0,
            "inserted": 0,
            "updated": 0,
            "errors": [],
        }

        if args.delete_sample_products:
            report["sample_products_deleted"] = await _delete_count(
                products_collection,
                SAMPLE_PRODUCTS_QUERY,
                dry_run=args.dry_run,
            )

        if args.replace_dataset:
            report["dataset_products_deleted"] = await _delete_count(
                products_collection,
                {"source": "dataset"},
                dry_run=args.dry_run,
            )

        if not args.file:
            report["products_total_after"] = await products_collection.count_documents({})
            return report

        preview = load_products_from_dataset(Path(args.file))
        report["rows_valid"] = len(preview.products)
        report["rows_invalid"] = len(preview.errors)
        report["errors"] = [
            {
                "row_number": error.row_number,
                "reason": error.reason,
            }
            for error in preview.errors[:20]
        ]

        if args.dry_run:
            report["preview_products"] = preview.products[:3]
            report["products_total_after"] = await products_collection.count_documents({})
            return report

        now = datetime.now(UTC)

        for product in preview.products:
            document = {
                **product,
                "updated_at": now,
                "imported_at": now,
            }

            result = await products_collection.update_one(
                {"external_id": product["external_id"]},
                {
                    "$set": document,
                    "$setOnInsert": {"created_at": now},
                },
                upsert=True,
            )

            if result.upserted_id is not None:
                report["inserted"] += 1
            else:
                report["updated"] += result.modified_count

        report["products_total_after"] = await products_collection.count_documents({})
        report["dataset_products_after"] = await products_collection.count_documents(
            {"source": "dataset"}
        )
        report["sample_like_products_after"] = await products_collection.count_documents(
            SAMPLE_PRODUCTS_QUERY
        )

        return report
    finally:
        await client.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import KOYASH product dataset into MongoDB.")
    parser.add_argument(
        "--file",
        default=None,
        help="Path to CSV/XLSX file. In Docker use /data/products.xlsx or /data/products.csv.",
    )
    parser.add_argument(
        "--replace-dataset",
        action="store_true",
        help="Delete existing products with source=dataset before import.",
    )
    parser.add_argument(
        "--delete-sample-products",
        action="store_true",
        help="Delete local sample/demo products.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and show import report without changing MongoDB.",
    )

    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    report = await import_products(args)
    print(json.dumps(report, ensure_ascii=False, indent=2, default=_json_default))


if __name__ == "__main__":
    asyncio.run(main())
