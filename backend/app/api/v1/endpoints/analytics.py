from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.v1.dependencies import get_optional_current_user
from app.db.mongodb import get_database
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import AnalyticsEventCreate, AnalyticsEventResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_analytics_service(database=Depends(get_database)) -> AnalyticsService:
    return AnalyticsService(
        analytics_repository=AnalyticsRepository(database),
    )


@router.post(
    "/events",
    response_model=AnalyticsEventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_event(
    payload: AnalyticsEventCreate,
    current_user: Annotated[dict | None, Depends(get_optional_current_user)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> AnalyticsEventResponse:
    return await service.record_public_event(
        payload,
        authenticated_user_id=(
            current_user["user_id"] if current_user is not None else None
        ),
    )
