from datetime import datetime
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductResponse(BaseModel):
    external_id: str
    name: str
    brand: str
    category: str
    routine_step: str
    price_rub: int = Field(ge=0)
    budget_segment: str
    skin_types: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    ingredients: list[str] = Field(default_factory=list)
    key_ingredients: list[str] = Field(default_factory=list)
    ingredient_highlights: str | None = None
    functional_category: str | None = None
    ingredient_flags: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    values: list[str] = Field(default_factory=list)
    texture: str | None = None
    description: str
    how_to_use: str
    image_url: str | None = None
    product_url: str | None = None
    ph: str | None = None
    vegan: bool = False
    cruelty_free: bool = False
    volume_ml: float | None = None
    price_per_ml: float | None = None
    source_url: str | None = None
    is_active: bool = True

    model_config = ConfigDict(extra="ignore")


class CatalogFacetValue(BaseModel):
    value: str
    count: int = Field(ge=0)


class ProductCatalogFacets(BaseModel):
    routine_steps: list[CatalogFacetValue] = Field(default_factory=list)
    budget_segments: list[CatalogFacetValue] = Field(default_factory=list)
    skin_types: list[CatalogFacetValue] = Field(default_factory=list)
    concerns: list[CatalogFacetValue] = Field(default_factory=list)
    values: list[CatalogFacetValue] = Field(default_factory=list)
    textures: list[CatalogFacetValue] = Field(default_factory=list)
    min_price_rub: int = Field(default=0, ge=0)
    max_price_rub: int = Field(default=0, ge=0)


class ProductCatalogResponse(BaseModel):
    items: list[ProductResponse] = Field(default_factory=list)
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total_pages: int = Field(ge=0)
    facets: ProductCatalogFacets


class ProductCatalogQualityResponse(BaseModel):
    total_products: int = Field(ge=0)
    active_products: int = Field(ge=0)
    inactive_products: int = Field(ge=0)
    dataset_products: int = Field(ge=0)
    strict_dataset_ok: bool
    step_counts: dict[str, int] = Field(default_factory=dict)
    budget_counts: dict[str, int] = Field(default_factory=dict)
    risk_flag_counts: dict[str, int] = Field(default_factory=dict)
    missing_field_counts: dict[str, int] = Field(default_factory=dict)
    completeness_percent: float = Field(ge=0, le=100)
    image_coverage_percent: float = Field(default=0, ge=0, le=100)
    product_link_coverage_percent: float = Field(default=0, ge=0, le=100)
    usage_coverage_percent: float = Field(default=0, ge=0, le=100)
    last_imported_at: datetime | None = None


CatalogIssue = Literal[
    "all",
    "inactive",
    "missing_ingredients",
    "missing_usage",
    "missing_image",
    "missing_product_link",
]


class ProductCatalogIssueItem(BaseModel):
    external_id: str
    name: str
    brand: str
    routine_step: str
    is_active: bool
    issues: list[str] = Field(default_factory=list)
    description: str = ""
    how_to_use: str = ""
    image_url: str | None = None
    product_url: str | None = None


class ProductCatalogIssueResponse(BaseModel):
    items: list[ProductCatalogIssueItem] = Field(default_factory=list)
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total_pages: int = Field(ge=0)


class AdminProductUpdate(BaseModel):
    description: str | None = Field(default=None, min_length=1, max_length=2000)
    how_to_use: str | None = Field(default=None, min_length=1, max_length=1000)
    image_url: str | None = Field(default=None, max_length=1000)
    product_url: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = None

    @field_validator("image_url", "product_url")
    @classmethod
    def validate_external_url(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        if not normalized:
            return ""

        parsed = urlparse(normalized)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
            raise ValueError("URL must be an absolute HTTP(S) address")
        return normalized


class AdminCatalogImportResponse(BaseModel):
    file_name: str
    fingerprint: str
    rows_valid: int = Field(ge=1)
    inserted: int = Field(ge=0)
    updated: int = Field(ge=0)
    deactivated: int = Field(ge=0)
    dataset_products_after: int = Field(ge=0)
    active_products_after: int = Field(ge=0)
    synchronize_missing: bool
    imported_at: datetime
