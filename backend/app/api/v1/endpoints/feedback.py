from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pymongo.asynchronous.database import AsyncDatabase

from app.api.v1.dependencies import get_optional_current_user
from app.db.mongodb import get_database
from app.schemas.feedback import FeedbackCreate
from app.services.feedback_service import FeedbackService
from app.services.recommendation_access_service import RecommendationAccessService

router = APIRouter(tags=["feedback"])


LEGACY_STRATEGY_BY_REASON = {
    "too_expensive": "cheaper_same_step",
    "dislikes_brand": "different_brand_same_step",
    "composition_concern": "safer_composition_same_step",
    "texture_not_suitable": "different_texture_same_step",
    "too_many_steps": "simpler_routine_same_step",
    "other": "general_same_step",
}


def get_feedback_service(
    database: Annotated[AsyncDatabase[Any], Depends(get_database)],
) -> FeedbackService:
    return FeedbackService(database)


@router.post("/recommendations/{recommendation_id}/feedback")
async def submit_feedback(
    recommendation_id: str,
    payload: FeedbackCreate,
    current_user: Annotated[dict | None, Depends(get_optional_current_user)],
    database: Annotated[AsyncDatabase[Any], Depends(get_database)],
    service: Annotated[FeedbackService, Depends(get_feedback_service)],
) -> dict[str, Any]:
    await RecommendationAccessService(database).require_access(
        recommendation_id,
        current_user=current_user,
        anonymous_id=payload.anonymous_id,
    )
    result = await service.submit_feedback(
        recommendation_id=recommendation_id,
        payload=payload,
    )

    data = result.model_dump(mode="json")
    replacement_strategy = LEGACY_STRATEGY_BY_REASON.get(
        data["reason"],
        "general_same_step",
    )

    replacement_session = {
        "replacement_session_id": data["replacement_session_id"],
        "recommendation_id": data["recommendation_id"],
        "feedback_id": data["feedback_id"],
        "original_product_external_id": data["product_external_id"],
        "reason": data["reason"],
        "replacement_strategy": replacement_strategy,
        "replacement_candidates": data["replacement_candidates"],
        "candidates": data["replacement_candidates"],
    }

    return {
        **data,

        # Legacy field expected by old tests/frontend.
        "replacement_strategy": replacement_strategy,

        # Legacy shape.
        "feedback": {
            "feedback_id": data["feedback_id"],
            "recommendation_id": data["recommendation_id"],
            "product_external_id": data["product_external_id"],
            "reason": data["reason"],
            "comment": data.get("comment"),
            "created_at": data["created_at"],
        },

        # New + legacy-compatible session shape.
        "replacement_session": replacement_session,
    }
