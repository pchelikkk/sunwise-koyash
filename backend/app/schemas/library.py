from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.product import ProductResponse
from app.schemas.recommendation import RecommendationResponse


class FavoriteProductResponse(BaseModel):
    product: ProductResponse
    created_at: datetime


class FavoriteProductListResponse(BaseModel):
    items: list[FavoriteProductResponse] = Field(default_factory=list)
    total: int = Field(ge=0)


class CosmeticBagProductResponse(BaseModel):
    product: ProductResponse
    created_at: datetime


class CosmeticBagProductListResponse(BaseModel):
    items: list[CosmeticBagProductResponse] = Field(default_factory=list)
    total: int = Field(ge=0)


class RecommendationHistoryResponse(BaseModel):
    items: list[RecommendationResponse] = Field(default_factory=list)
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
