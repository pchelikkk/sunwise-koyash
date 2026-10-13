from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pymongo.asynchronous.database import AsyncDatabase

from app.api.v1.dependencies import get_optional_current_user
from app.db.mongodb import get_database
from app.schemas.replacement import (
    ReplacementSelectionRequest,
    ReplacementSelectionResponse,
)
from app.services.recommendation_access_service import RecommendationAccessService
from app.services.replacement_service import ReplacementService

router = APIRouter(tags=["replacements"])


LEGACY_STRATEGY_BY_REASON = {
    "too_expensive": "cheaper_same_step",
    "dislikes_brand": "different_brand_same_step",
    "composition_concern": "safer_composition_same_step",
    "texture_not_suitable": "different_texture_same_step",
    "too_many_steps": "simpler_routine_same_step",
    "other": "general_same_step",
}


def get_replacement_service(
    database: Annotated[AsyncDatabase[Any], Depends(get_database)],
) -> ReplacementService:
    return ReplacementService(database)


@router.get("/recommendations/{recommendation_id}/replacements")
async def list_replacements(
    recommendation_id: str,
    current_user: Annotated[dict | None, Depends(get_optional_current_user)],
    database: Annotated[AsyncDatabase[Any], Depends(get_database)],
    service: Annotated[ReplacementService, Depends(get_replacement_service)],
    anonymous_id: Annotated[str | None, Query(max_length=120)] = None,
) -> dict[str, Any]:
    await RecommendationAccessService(database).require_access(
        recommendation_id,
        current_user=current_user,
        anonymous_id=anonymous_id,
    )
    sessions = await service.list_sessions(recommendation_id)
    data = []

    for session in sessions:
        item = session.model_dump(mode="json")
        candidates = item.get("replacement_candidates", [])
        reason = item.get("reason", "other")
        replacement_strategy = LEGACY_STRATEGY_BY_REASON.get(reason, "general_same_step")

        # Legacy aliases for old frontend/tests.
        item["candidates"] = candidates
        item["replacement_strategy"] = replacement_strategy

        data.append(item)

    return {
        "replacements": data,
        "items": data,
        "total": len(data),
    }


@router.post(
    "/recommendations/{recommendation_id}/replacements/{session_id}/select",
    response_model=ReplacementSelectionResponse,
)
async def select_replacement(
    recommendation_id: str,
    session_id: str,
    payload: ReplacementSelectionRequest,
    current_user: Annotated[dict | None, Depends(get_optional_current_user)],
    database: Annotated[AsyncDatabase[Any], Depends(get_database)],
    service: Annotated[ReplacementService, Depends(get_replacement_service)],
) -> ReplacementSelectionResponse:
    await RecommendationAccessService(database).require_access(
        recommendation_id,
        current_user=current_user,
        anonymous_id=payload.anonymous_id,
    )
    return await service.select_replacement(
        recommendation_id=recommendation_id,
        session_id=session_id,
        product_external_id=payload.product_external_id,
    )
