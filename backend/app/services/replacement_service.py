from typing import Any

from fastapi import HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase

from app.algorithms.scoring import ScoredProduct, score_product
from app.core.enums import AnalyticsEventType
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.replacement_repository import ReplacementRepository
from app.schemas.recommendation import RecommendationRequest, RecommendationRoutine
from app.schemas.replacement import ReplacementSelectionResponse, ReplacementSessionResponse
from app.services.event_tracking_service import EventTrackingService
from app.services.explanation_service import ExplanationService
from app.services.llm_explanation_service import LLMExplanationService


class ReplacementService:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.repository = ReplacementRepository(database)
        self.recommendation_repository = RecommendationRepository(database)
        self.explanation_service = ExplanationService()
        self.event_tracking_service = EventTrackingService(
            AnalyticsRepository(database),
        )
        self.llm_explanation_service = LLMExplanationService(
            self.event_tracking_service,
        )

    async def list_sessions(
        self,
        recommendation_id: str,
    ) -> list[ReplacementSessionResponse]:
        sessions = await self.repository.list_by_recommendation(recommendation_id)
        return [ReplacementSessionResponse(**session) for session in sessions]

    async def select_replacement(
        self,
        *,
        recommendation_id: str,
        session_id: str,
        product_external_id: str,
    ) -> ReplacementSelectionResponse:
        session = await self.repository.find_by_id(session_id)

        if session is None or session["recommendation_id"] != recommendation_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Replacement session not found",
            )

        if session.get("selected_product_external_id"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A replacement has already been applied for this session",
            )

        candidates = session.get("replacement_candidates", [])
        selected_candidate = next(
            (
                candidate
                for candidate in candidates
                if candidate.get("product", {}).get("external_id")
                == product_external_id
            ),
            None,
        )

        if selected_candidate is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected product is not part of replacement candidates",
            )

        recommendation = await self.recommendation_repository.find_by_id(
            recommendation_id
        )
        if recommendation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recommendation not found",
            )

        request = RecommendationRequest(**recommendation["request"])
        candidate_product = selected_candidate["product"]
        replacement_item = self.explanation_service.build_recommended_product(
            ScoredProduct(
                product=candidate_product,
                score=score_product(candidate_product, request),
            ),
            request,
        )
        replacement_item = await self.llm_explanation_service.enhance_recommended_product(
            replacement_item,
            request,
            user_id=recommendation.get("user_id"),
            anonymous_id=recommendation.get("anonymous_id"),
        )

        original_product_external_id = session["original_product_external_id"]
        updated_recommendation = (
            await self.recommendation_repository.replace_routine_product(
                recommendation_id=recommendation_id,
                original_product_external_id=original_product_external_id,
                replacement_item=replacement_item.model_dump(),
            )
        )
        if updated_recommendation is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The original product is no longer part of this recommendation",
            )

        updated = await self.repository.select(
            session_id=session_id,
            product_external_id=product_external_id,
        )

        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Replacement session not found",
            )

        await self.event_tracking_service.record(
            AnalyticsEventType.REPLACEMENT_SELECTED,
            user_id=recommendation.get("user_id"),
            anonymous_id=recommendation.get("anonymous_id"),
            recommendation_id=recommendation_id,
            product_external_id=product_external_id,
            metadata={
                "replacement_session_id": session_id,
                "feedback_id": session.get("feedback_id"),
                "original_product_external_id": session.get(
                    "original_product_external_id"
                ),
                "reason": session.get("reason"),
            },
        )

        return ReplacementSelectionResponse(
            replacement_session_id=session_id,
            original_product_external_id=original_product_external_id,
            selected_product_external_id=product_external_id,
            replacement_item=replacement_item,
            routine=RecommendationRoutine(**updated_recommendation["routine"]),
            total_price_rub=updated_recommendation["total_price_rub"],
        )
