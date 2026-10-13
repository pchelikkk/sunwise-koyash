from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.recommendation import RecommendationRoutine, RecommendedProduct


class ReplacementCandidate(BaseModel):
    rank: int
    product: dict[str, Any]
    reason: str
    replacement_score: int
    why_better: str
    replacement_reason: str


class ReplacementSessionResponse(BaseModel):
    replacement_session_id: str
    feedback_id: str
    recommendation_id: str
    original_product_external_id: str
    reason: str
    replacement_candidates: list[ReplacementCandidate] = Field(default_factory=list)
    selected_product_external_id: str | None = None
    created_at: datetime
    updated_at: datetime


class ReplacementSelectionRequest(BaseModel):
    product_external_id: str = Field(min_length=1)
    anonymous_id: str | None = Field(default=None, max_length=120)


class ReplacementSelectionResponse(BaseModel):
    replacement_session_id: str
    original_product_external_id: str
    selected_product_external_id: str
    replacement_item: RecommendedProduct
    routine: RecommendationRoutine
    total_price_rub: int
    status: str = "selected"
