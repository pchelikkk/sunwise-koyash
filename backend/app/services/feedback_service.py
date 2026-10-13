from typing import Any

from bson import ObjectId
from fastapi import HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase

from app.algorithms.replacement_strategy import build_replacement_candidates
from app.core.enums import AnalyticsEventType
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.replacement_repository import ReplacementRepository
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.services.event_tracking_service import EventTrackingService


class FeedbackService:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.database = database
        self.feedback_repository = FeedbackRepository(database)
        self.replacement_repository = ReplacementRepository(database)
        self.event_tracking_service = EventTrackingService(
            AnalyticsRepository(database),
        )

    async def submit_feedback(
        self,
        *,
        recommendation_id: str,
        payload: FeedbackCreate,
    ) -> FeedbackResponse:
        recommendation = await self._find_recommendation(recommendation_id)

        if recommendation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recommendation not found",
            )

        original_item = await self._find_original_item(
            recommendation=recommendation,
            product_external_id=payload.product_external_id,
        )

        if original_item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product is not part of this recommendation",
            )

        recommendation_anonymous_id = recommendation.get("anonymous_id")

        feedback = await self.feedback_repository.create(
            recommendation_id=recommendation_id,
            product_external_id=payload.product_external_id,
            reason=payload.reason,
            comment=payload.comment,
            anonymous_id=recommendation_anonymous_id,
        )

        products = await self.database["products"].find({"is_active": True}).to_list(length=None)

        candidates = build_replacement_candidates(
            original_item=original_item,
            products=products,
            reason=payload.reason,
            recommendation=recommendation,
            limit=3,
        )

        session = await self.replacement_repository.create(
            recommendation_id=recommendation_id,
            feedback_id=feedback["feedback_id"],
            original_product_external_id=payload.product_external_id,
            reason=payload.reason,
            candidates=candidates,
        )

        user_id = recommendation.get("user_id")
        anonymous_id = recommendation_anonymous_id
        candidate_ids = [
            candidate["product"]["external_id"]
            for candidate in candidates
            if candidate.get("product", {}).get("external_id")
        ]
        replacement_status = "available" if candidate_ids else "not_found"
        replacement_message = (
            "Нашли несколько подходящих вариантов — выбранный заменит средство прямо в подборе."
            if candidate_ids
            else (
                "Сейчас не нашли безопасную замену с теми же условиями. "
                "Отзыв сохранён — попробуй изменить фильтры или выбрать другое средство в каталоге."
            )
        )

        await self.event_tracking_service.record(
            AnalyticsEventType.FEEDBACK_SUBMITTED,
            user_id=user_id,
            anonymous_id=anonymous_id,
            recommendation_id=recommendation_id,
            product_external_id=payload.product_external_id,
            metadata={
                "feedback_id": feedback["feedback_id"],
                "replacement_session_id": session["replacement_session_id"],
                "reason": payload.reason,
                "has_comment": bool(payload.comment and payload.comment.strip()),
            },
        )

        await self.event_tracking_service.record(
            AnalyticsEventType.REPLACEMENT_GENERATED,
            user_id=user_id,
            anonymous_id=anonymous_id,
            recommendation_id=recommendation_id,
            product_external_id=payload.product_external_id,
            metadata={
                "feedback_id": feedback["feedback_id"],
                "replacement_session_id": session["replacement_session_id"],
                "reason": payload.reason,
                "candidate_count": len(candidate_ids),
                "candidate_product_ids": candidate_ids,
            },
        )

        return FeedbackResponse(
            feedback_id=feedback["feedback_id"],
            recommendation_id=recommendation_id,
            product_external_id=payload.product_external_id,
            reason=payload.reason,
            comment=payload.comment,
            replacement_session_id=session["replacement_session_id"],
            replacement_candidates=session["replacement_candidates"],
            replacement_status=replacement_status,
            replacement_message=replacement_message,
            created_at=feedback["created_at"],
        )

    async def _find_recommendation(self, recommendation_id: str) -> dict[str, Any] | None:
        collections_to_try = [
            "recommendation_sessions",
            "recommendations",
        ]

        queries: list[dict[str, Any]] = [
            {"recommendation_id": recommendation_id},
            {"session_id": recommendation_id},
            {"id": recommendation_id},
        ]

        if ObjectId.is_valid(recommendation_id):
            object_id = ObjectId(recommendation_id)
            queries.insert(0, {"_id": object_id})
            queries.append({"recommendation_id": object_id})
            queries.append({"session_id": object_id})

        queries.append({"_id": recommendation_id})

        for collection_name in collections_to_try:
            collection = self.database[collection_name]

            for query in queries:
                document = await collection.find_one(query)
                if document is not None:
                    document["recommendation_id"] = str(
                        document.get("recommendation_id")
                        or document.get("session_id")
                        or document.get("_id")
                        or recommendation_id
                    )
                    return document

        return None

    async def _find_original_item(
        self,
        *,
        recommendation: dict[str, Any],
        product_external_id: str,
    ) -> dict[str, Any] | None:
        for item in self._routine_items(recommendation):
            product = item.get("product") if isinstance(item, dict) else None
            product = product if isinstance(product, dict) else {}

            possible_ids = {
                str(product.get("external_id") or ""),
                str(product.get("product_external_id") or ""),
                str(product.get("id") or ""),
                str(item.get("product_external_id") or ""),
                str(item.get("external_id") or ""),
                str(item.get("product_id") or ""),
            }

            if product_external_id in possible_ids:
                if not product:
                    product = await self.database["products"].find_one(
                        {"external_id": product_external_id}
                    )
                    if product is not None:
                        item["product"] = product

                return item

        return None

    def _routine_items(self, recommendation: dict[str, Any]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []

        routine = recommendation.get("routine")
        if isinstance(routine, dict):
            for slot in ("morning", "evening", "items"):
                values = routine.get(slot)
                if isinstance(values, list):
                    items.extend([item for item in values if isinstance(item, dict)])

        for key in (
            "morning",
            "evening",
            "morning_routine",
            "evening_routine",
            "items",
            "routine_items",
            "recommendations",
        ):
            values = recommendation.get(key)
            if isinstance(values, list):
                items.extend([item for item in values if isinstance(item, dict)])

        result = recommendation.get("result")
        if isinstance(result, dict):
            result_routine = result.get("routine")
            if isinstance(result_routine, dict):
                for slot in ("morning", "evening", "items"):
                    values = result_routine.get(slot)
                    if isinstance(values, list):
                        items.extend([item for item in values if isinstance(item, dict)])

        return items
