from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pymongo.asynchronous.database import AsyncDatabase

from app.api.v1.dependencies import get_optional_current_user
from app.db.mongodb import get_database
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.services.event_tracking_service import EventTrackingService
from app.services.explanation_service import ExplanationService
from app.services.llm_explanation_service import LLMExplanationService
from app.services.recommendation_access_service import RecommendationAccessService
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def get_recommendation_service(
    database: Annotated[AsyncDatabase[Any], Depends(get_database)],
) -> RecommendationService:
    event_tracking_service = EventTrackingService(AnalyticsRepository(database))
    return RecommendationService(
        product_repository=ProductRepository(database),
        recommendation_repository=RecommendationRepository(database),
        explanation_service=ExplanationService(),
        event_tracking_service=event_tracking_service,
        llm_explanation_service=LLMExplanationService(event_tracking_service),
    )


@router.post("", response_model=RecommendationResponse)
async def create_recommendation(
    payload: RecommendationRequest,
    current_user: Annotated[dict | None, Depends(get_optional_current_user)],
    service: Annotated[RecommendationService, Depends(get_recommendation_service)],
) -> RecommendationResponse:
    return await service.create_recommendation(
        payload,
        user_id=current_user["user_id"] if current_user is not None else None,
        authenticated_anonymous_id=(
            current_user.get("anonymous_id") if current_user is not None else None
        ),
    )


@router.get("/{recommendation_id}", response_model=RecommendationResponse)
async def get_recommendation(
    recommendation_id: str,
    current_user: Annotated[dict | None, Depends(get_optional_current_user)],
    database: Annotated[AsyncDatabase[Any], Depends(get_database)],
    service: Annotated[RecommendationService, Depends(get_recommendation_service)],
    anonymous_id: Annotated[str | None, Query(max_length=120)] = None,
) -> RecommendationResponse:
    await RecommendationAccessService(database).require_access(
        recommendation_id,
        current_user=current_user,
        anonymous_id=anonymous_id,
    )
    recommendation = await service.get_recommendation(recommendation_id)

    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found",
        )

    return recommendation
