import asyncio

from app.algorithms.filters import apply_hard_filters
from app.algorithms.normalizer import normalized_request
from app.algorithms.routine_builder import build_routine
from app.algorithms.scoring import score_products
from app.algorithms.skin_diagnosis import diagnose_skin_type, self_reported_skin_type
from app.algorithms.sorting import sort_scored_products
from app.core.enums import AnalyticsEventType
from app.core.time import utc_now
from app.repositories.product_repository import ProductRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.schemas.recommendation import (
    FilterSummary,
    RecommendationRequest,
    RecommendationResponse,
    RecommendationRoutine,
    RestrictionCoverage,
    RestrictionMatch,
)
from app.services.event_tracking_service import EventTrackingService
from app.services.explanation_service import ExplanationService
from app.services.llm_explanation_service import LLMExplanationService


class RecommendationService:
    algorithm_version = "rule-based-v2"

    def __init__(
        self,
        product_repository: ProductRepository,
        recommendation_repository: RecommendationRepository,
        explanation_service: ExplanationService,
        event_tracking_service: EventTrackingService | None = None,
        llm_explanation_service: LLMExplanationService | None = None,
    ) -> None:
        self.product_repository = product_repository
        self.recommendation_repository = recommendation_repository
        self.explanation_service = explanation_service
        self.event_tracking_service = event_tracking_service
        self.llm_explanation_service = llm_explanation_service

    async def create_recommendation(
        self,
        request: RecommendationRequest,
        *,
        user_id: str | None = None,
        authenticated_anonymous_id: str | None = None,
    ) -> RecommendationResponse:
        submitted_skin_type = request.skin_type.strip().lower()
        if submitted_skin_type == "unknown":
            if request.skin_diagnostic_answers is None:
                raise ValueError("Skin diagnostic answers are required")
            skin_profile = diagnose_skin_type(request.skin_diagnostic_answers)
            effective_request = request.model_copy(
                update={"skin_type": skin_profile.resolved_skin_type}
            )
        else:
            skin_profile = self_reported_skin_type(submitted_skin_type)
            effective_request = request

        normalized = normalized_request(effective_request)
        session_anonymous_id = (
            authenticated_anonymous_id if user_id is not None else normalized.anonymous_id
        )
        request_payload = normalized.model_dump()
        request_payload["anonymous_id"] = session_anonymous_id

        products = await self.product_repository.list_active_products()
        filter_result = apply_hard_filters(products=products, request=normalized)

        scored = score_products(filter_result.allowed_products, normalized)
        sorted_products = sort_scored_products(scored)

        routine_source = build_routine(
            products=sorted_products,
            experience=normalized.experience,
            routine_preference=normalized.routine_preference,
        )

        routine = RecommendationRoutine(
            morning=[
                self.explanation_service.build_recommended_product(item, normalized)
                for item in routine_source["morning"]
            ],
            evening=[
                self.explanation_service.build_recommended_product(item, normalized)
                for item in routine_source["evening"]
            ],
        )

        if self.llm_explanation_service is not None:
            routine = await self._enhance_explanations(
                routine,
                normalized,
                user_id=user_id,
                anonymous_id=session_anonymous_id,
            )

        unique_products = {
            item.product.external_id: item.product for item in [*routine.morning, *routine.evening]
        }

        total_price_rub = sum(product.price_rub for product in unique_products.values())

        restriction_match_counts = filter_result.restriction_match_counts
        matched_restrictions = [
            restriction
            for restriction, match_count in restriction_match_counts.items()
            if match_count > 0
        ]
        unmatched_restrictions = [
            restriction
            for restriction, match_count in restriction_match_counts.items()
            if match_count == 0
        ]

        filter_summary = FilterSummary(
            total_products=len(products),
            allowed_products=len(filter_result.allowed_products),
            filtered_out=len(products) - len(filter_result.allowed_products),
            filter_reasons=filter_result.filter_reasons,
            restriction_coverage=RestrictionCoverage(
                requested_restrictions=list(restriction_match_counts),
                matched_restrictions=matched_restrictions,
                unmatched_restrictions=unmatched_restrictions,
                matches=[
                    RestrictionMatch(
                        restriction=restriction,
                        matched_product_count=match_count,
                    )
                    for restriction, match_count in restriction_match_counts.items()
                ],
            ),
        )

        result_payload = {
            "algorithm_version": self.algorithm_version,
            "skin_profile": skin_profile.model_dump(),
            "routine": routine.model_dump(),
            "filter_summary": filter_summary.model_dump(),
            "total_price_rub": total_price_rub,
            "created_at": utc_now(),
        }

        recommendation_id = await self.recommendation_repository.save_session(
            request=request_payload,
            result=result_payload,
            algorithm_version=self.algorithm_version,
            anonymous_id=session_anonymous_id,
            user_id=user_id,
        )

        if self.event_tracking_service is not None:
            await self.event_tracking_service.record(
                AnalyticsEventType.QUESTIONNAIRE_COMPLETED,
                user_id=user_id,
                anonymous_id=session_anonymous_id,
                recommendation_id=recommendation_id,
                metadata={
                    "age_group": self._age_group(normalized.age),
                    "skin_type": normalized.skin_type,
                    "skin_type_source": skin_profile.method,
                    "skin_type_confidence": skin_profile.confidence,
                    "concerns": normalized.concerns,
                    "primary_concern": normalized.primary_concern,
                    "sensitivity_level": normalized.sensitivity_level,
                    "budget": normalized.budget,
                    "excluded_ingredients": normalized.excluded_ingredients,
                    "custom_restriction_count": len(normalized.custom_restrictions),
                    "experience": normalized.experience,
                    "routine_preference": normalized.routine_preference,
                    "texture_preference": normalized.texture_preference,
                    "values": normalized.values,
                },
            )

            await self.event_tracking_service.record(
                AnalyticsEventType.RECOMMENDATION_GENERATED,
                user_id=user_id,
                anonymous_id=session_anonymous_id,
                recommendation_id=recommendation_id,
                metadata={
                    "algorithm_version": self.algorithm_version,
                    "allowed_products": filter_summary.allowed_products,
                    "filtered_out": filter_summary.filtered_out,
                    "filter_reasons": filter_summary.filter_reasons,
                    "unmatched_restriction_count": len(unmatched_restrictions),
                    "total_price_rub": total_price_rub,
                    "routine_product_count": len(unique_products),
                    "morning_count": len(routine.morning),
                    "evening_count": len(routine.evening),
                    "product_external_ids": sorted(unique_products),
                },
            )

        return RecommendationResponse(
            recommendation_id=recommendation_id,
            **result_payload,
        )

    async def get_recommendation(self, recommendation_id: str) -> RecommendationResponse | None:
        document = await self.recommendation_repository.find_by_id(recommendation_id)

        if document is None:
            return None

        return RecommendationResponse(
            recommendation_id=document["recommendation_id"],
            **document["result"],
        )

    async def _enhance_explanations(
        self,
        routine: RecommendationRoutine,
        request: RecommendationRequest,
        *,
        user_id: str | None,
        anonymous_id: str | None,
    ) -> RecommendationRoutine:
        service = self.llm_explanation_service
        if service is None or not service.is_configured:
            return routine

        unique_items = {
            item.product.external_id: item
            for item in [*routine.morning, *routine.evening]
        }
        enhanced = await asyncio.gather(
            *(
                service.enhance_recommended_product(
                    item,
                    request,
                    user_id=user_id,
                    anonymous_id=anonymous_id,
                )
                for item in unique_items.values()
            )
        )
        by_product_id = {
            item.product.external_id: item
            for item in enhanced
        }
        return RecommendationRoutine(
            morning=[by_product_id[item.product.external_id] for item in routine.morning],
            evening=[by_product_id[item.product.external_id] for item in routine.evening],
        )

    @staticmethod
    def _age_group(age: int | None) -> str | None:
        if age is None:
            return None
        if age < 18:
            return "12-17"
        if age < 25:
            return "18-24"
        if age < 35:
            return "25-34"
        if age < 45:
            return "35-44"
        return "45+"
