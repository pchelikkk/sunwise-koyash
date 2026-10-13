import hashlib
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from fastapi import HTTPException, status
from pymongo import UpdateOne
from pymongo.asynchronous.database import AsyncDatabase

from app.importers.product_dataset import SUPPORTED_EXTENSIONS, load_products_from_dataset
from app.importers.product_dataset_sync import DATASET_STATE_ID
from app.schemas.product import AdminCatalogImportResponse

MAX_DATASET_FILE_BYTES = 10 * 1024 * 1024
MAX_DATASET_ROWS = 5_000


class CatalogImportService:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.database = database

    async def import_dataset(
        self,
        *,
        file_name: str,
        content: bytes,
        synchronize_missing: bool,
        admin_user_id: str,
    ) -> AdminCatalogImportResponse:
        safe_file_name = Path(file_name or "dataset").name
        suffix = Path(safe_file_name).suffix.lower()

        if suffix not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Поддерживаются только файлы .xlsx и .csv.",
            )
        if not content:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Файл пуст.",
            )
        if len(content) > MAX_DATASET_FILE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Размер датасета не должен превышать 10 МБ.",
            )

        preview = self._preview(content, suffix)
        if preview.errors:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "message": "Импорт отменён: исправьте ошибки в датасете.",
                    "rows_valid": len(preview.products),
                    "rows_invalid": len(preview.errors),
                    "errors": [
                        {
                            "row_number": error.row_number,
                            "reason": error.reason,
                        }
                        for error in preview.errors[:20]
                    ],
                },
            )
        if not preview.products:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="В файле нет валидных товаров.",
            )
        if len(preview.products) > MAX_DATASET_ROWS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"За один импорт поддерживается не более {MAX_DATASET_ROWS} товаров.",
            )

        external_ids = [str(product["external_id"]) for product in preview.products]
        duplicate_ids = sorted(
            external_id
            for external_id, count in Counter(external_ids).items()
            if count > 1
        )
        if duplicate_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "message": "Импорт отменён: external_id должен быть уникальным.",
                    "duplicate_external_ids": duplicate_ids[:20],
                },
            )

        fingerprint = hashlib.sha256(content).hexdigest()
        imported_at = datetime.now(UTC)
        products = self.database["products"]
        existing_ids = set(
            await products.distinct(
                "external_id",
                {"external_id": {"$in": external_ids}},
            )
        )
        operations = [
            UpdateOne(
                {"external_id": product["external_id"]},
                {
                    "$set": {
                        **product,
                        "dataset_fingerprint": fingerprint,
                        "imported_at": imported_at,
                        "updated_at": imported_at,
                        "updated_by": admin_user_id,
                    },
                    "$unset": {"deactivated_by_import": ""},
                    "$setOnInsert": {"created_at": imported_at},
                },
                upsert=True,
            )
            for product in preview.products
        ]
        await products.bulk_write(operations, ordered=True)

        deactivated = 0
        if synchronize_missing:
            result = await products.update_many(
                {
                    "source": "dataset",
                    "external_id": {"$nin": external_ids},
                    "is_active": {"$ne": False},
                },
                {
                    "$set": {
                        "is_active": False,
                        "deactivated_by_import": fingerprint,
                        "updated_at": imported_at,
                        "updated_by": admin_user_id,
                    }
                },
            )
            deactivated = int(result.modified_count)

        dataset_products_after = await products.count_documents({"source": "dataset"})
        active_products_after = await products.count_documents(
            {"source": "dataset", "is_active": True}
        )
        await self.database["catalog_import_state"].update_one(
            {"_id": DATASET_STATE_ID},
            {
                "$set": {
                    "source": "admin_upload",
                    "fingerprint": fingerprint,
                    "file_name": safe_file_name,
                    "product_count": dataset_products_after,
                    "uploaded_rows": len(preview.products),
                    "synchronize_missing": synchronize_missing,
                    "synced_at": imported_at,
                    "uploaded_by": admin_user_id,
                },
                "$unset": {"path": ""},
            },
            upsert=True,
        )
        await self.database["admin_audit_events"].insert_one(
            {
                "event_type": "catalog_dataset_imported",
                "admin_user_id": admin_user_id,
                "file_name": safe_file_name,
                "file_size_bytes": len(content),
                "fingerprint": fingerprint,
                "external_ids": external_ids[:100],
                "rows_valid": len(preview.products),
                "inserted": sum(external_id not in existing_ids for external_id in external_ids),
                "updated": sum(external_id in existing_ids for external_id in external_ids),
                "deactivated": deactivated,
                "synchronize_missing": synchronize_missing,
                "created_at": imported_at,
            }
        )

        return AdminCatalogImportResponse(
            file_name=safe_file_name,
            fingerprint=fingerprint,
            rows_valid=len(preview.products),
            inserted=sum(external_id not in existing_ids for external_id in external_ids),
            updated=sum(external_id in existing_ids for external_id in external_ids),
            deactivated=deactivated,
            dataset_products_after=dataset_products_after,
            active_products_after=active_products_after,
            synchronize_missing=synchronize_missing,
            imported_at=imported_at,
        )

    @staticmethod
    def _preview(content: bytes, suffix: str):
        temporary_path: Path | None = None
        try:
            with NamedTemporaryFile(suffix=suffix, delete=False) as temporary:
                temporary.write(content)
                temporary_path = Path(temporary.name)
            return load_products_from_dataset(temporary_path)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
