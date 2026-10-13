from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pymongo.asynchronous.database import AsyncDatabase

from app.db.mongodb import get_database
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCatalogResponse, ProductResponse
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/catalog", response_model=ProductCatalogResponse)
async def product_catalog(
    database: Annotated[AsyncDatabase[Any], Depends(get_database)],
    search: Annotated[str | None, Query(max_length=100)] = None,
    routine_step: Annotated[list[str] | None, Query()] = None,
    budget_segment: Annotated[list[str] | None, Query()] = None,
    skin_type: Annotated[list[str] | None, Query()] = None,
    concern: Annotated[list[str] | None, Query()] = None,
    value: Annotated[list[str] | None, Query()] = None,
    min_price_rub: Annotated[int | None, Query(ge=0, le=1_000_000)] = None,
    max_price_rub: Annotated[int | None, Query(ge=0, le=1_000_000)] = None,
    no_known_irritants: bool = False,
    sort: Literal["relevance", "price_asc", "price_desc", "name"] = "relevance",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=48)] = 12,
) -> ProductCatalogResponse:
    if min_price_rub is not None and max_price_rub is not None and min_price_rub > max_price_rub:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="min_price_rub must not exceed max_price_rub",
        )

    service = ProductService(ProductRepository(database))
    return await service.catalog(
        search=search,
        routine_steps=routine_step or [],
        budget_segments=budget_segment or [],
        skin_types=skin_type or [],
        concerns=concern or [],
        values=value or [],
        min_price_rub=min_price_rub,
        max_price_rub=max_price_rub,
        no_known_irritants=no_known_irritants,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.get("", response_model=list[ProductResponse])
async def list_products(
    database: Annotated[AsyncDatabase[Any], Depends(get_database)],
    routine_step: str | None = Query(default=None),
    budget_segment: str | None = Query(default=None),
) -> list[ProductResponse]:
    service = ProductService(ProductRepository(database))
    products = await service.list_products(
        routine_step=routine_step,
        budget_segment=budget_segment,
    )
    return [ProductResponse(**product) for product in products]


@router.get("/{external_id}", response_model=ProductResponse)
async def get_product(
    external_id: str,
    database: Annotated[AsyncDatabase[Any], Depends(get_database)],
) -> ProductResponse:
    service = ProductService(ProductRepository(database))
    product = await service.get_product(external_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return ProductResponse(**product)
