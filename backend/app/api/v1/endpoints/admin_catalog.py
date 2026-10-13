from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pymongo.asynchronous.database import AsyncDatabase

from app.api.v1.dependencies import require_admin
from app.core.time import utc_now
from app.db.mongodb import get_database
from app.repositories.product_repository import ProductRepository
from app.schemas.product import (
    AdminCatalogImportResponse,
    AdminProductUpdate,
    CatalogIssue,
    ProductCatalogIssueResponse,
    ProductCatalogQualityResponse,
    ProductResponse,
)
from app.services.catalog_import_service import MAX_DATASET_FILE_BYTES, CatalogImportService
from app.services.product_service import ProductService

router = APIRouter(prefix="/admin/catalog", tags=["admin catalog"])


@router.post("/import", response_model=AdminCatalogImportResponse)
async def import_catalog_dataset(
    current_admin: Annotated[dict, Depends(require_admin)],
    database: Annotated[AsyncDatabase[Any], Depends(get_database)],
    file: Annotated[UploadFile, File(description="CSV or XLSX product dataset")],
    synchronize_missing: Annotated[bool, Form()] = True,
) -> AdminCatalogImportResponse:
    content = await file.read(MAX_DATASET_FILE_BYTES + 1)
    return await CatalogImportService(database).import_dataset(
        file_name=file.filename or "dataset",
        content=content,
        synchronize_missing=synchronize_missing,
        admin_user_id=current_admin["user_id"],
    )


@router.get(
    "/quality",
    response_model=ProductCatalogQualityResponse,
)
async def catalog_quality(
    _current_admin: Annotated[dict, Depends(require_admin)],
    database: Annotated[AsyncDatabase[Any], Depends(get_database)],
) -> ProductCatalogQualityResponse:
    return await ProductService(ProductRepository(database)).catalog_quality()


@router.get("/issues", response_model=ProductCatalogIssueResponse)
async def catalog_issues(
    _current_admin: Annotated[dict, Depends(require_admin)],
    database: Annotated[AsyncDatabase[Any], Depends(get_database)],
    issue: CatalogIssue = "all",
    search: Annotated[str | None, Query(max_length=100)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> ProductCatalogIssueResponse:
    return await ProductService(ProductRepository(database)).catalog_issues(
        issue=issue,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.patch("/products/{external_id}", response_model=ProductResponse)
async def update_product_content(
    external_id: str,
    payload: AdminProductUpdate,
    current_admin: Annotated[dict, Depends(require_admin)],
    database: Annotated[AsyncDatabase[Any], Depends(get_database)],
) -> ProductResponse:
    changes = payload.model_dump(exclude_none=True)
    if not changes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="At least one product field must be provided",
        )

    repository = ProductRepository(database)
    current = await repository.find_any_by_external_id(external_id)
    if current is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    effective_changes = {
        key: value for key, value in changes.items() if current.get(key) != value
    }
    if not effective_changes:
        return ProductResponse(**current)

    now = utc_now()
    updated = await repository.update_admin_fields(
        external_id,
        {
            **effective_changes,
            "updated_at": now,
            "updated_by": current_admin["user_id"],
        },
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    await database["admin_audit_events"].insert_one(
        {
            "event_type": "catalog_product_updated",
            "admin_user_id": current_admin["user_id"],
            "product_external_id": external_id,
            "changes": {
                key: {"before": current.get(key), "after": value}
                for key, value in effective_changes.items()
            },
            "created_at": now,
        }
    )
    return ProductResponse(**updated)
