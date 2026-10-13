from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

FeedbackReason = Literal[
    "too_expensive",
    "dislikes_brand",
    "composition_concern",
    "texture_not_suitable",
    "too_many_steps",
    "other",
]


class FeedbackCreate(BaseModel):
    product_external_id: str = Field(min_length=1)
    reason: FeedbackReason
    comment: str | None = Field(default=None, max_length=1000)
    anonymous_id: str | None = Field(default=None, max_length=120)


class FeedbackResponse(BaseModel):
    feedback_id: str
    recommendation_id: str
    product_external_id: str
    reason: FeedbackReason
    comment: str | None = None
    replacement_session_id: str
    replacement_candidates: list[dict[str, Any]] = Field(default_factory=list)
    replacement_status: Literal["available", "not_found"]
    replacement_message: str
    created_at: datetime
