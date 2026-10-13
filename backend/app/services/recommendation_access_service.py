import hmac
from typing import Any

from fastapi import HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase

from app.repositories.recommendation_repository import RecommendationRepository


class RecommendationAccessService:
    """Authorize access to a saved recommendation without exposing its existence."""

    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.repository = RecommendationRepository(database)

    async def require_access(
        self,
        recommendation_id: str,
        *,
        current_user: dict | None,
        anonymous_id: str | None,
    ) -> dict[str, Any]:
        recommendation = await self.repository.find_by_id(recommendation_id)
        if recommendation is None:
            self._not_found()

        owner_user_id = str(recommendation.get("user_id") or "")
        actor_user_id = str((current_user or {}).get("user_id") or "")

        if owner_user_id:
            if not actor_user_id or not hmac.compare_digest(owner_user_id, actor_user_id):
                self._not_found()
            return recommendation

        owner_anonymous_id = str(recommendation.get("anonymous_id") or "")
        actor_anonymous_id = str(anonymous_id or "")

        if owner_anonymous_id and (
            not actor_anonymous_id
            or not hmac.compare_digest(owner_anonymous_id, actor_anonymous_id)
        ):
            self._not_found()

        # Sessions created by old clients without either identity remain readable by
        # their unguessable id. New browser sessions always carry anonymous_id.
        return recommendation

    @staticmethod
    def _not_found() -> None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found",
        )
