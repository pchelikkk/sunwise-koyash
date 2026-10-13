import logging
from datetime import UTC, datetime, time, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pymongo.asynchronous.database import AsyncDatabase

from app.api.v1.dependencies import require_admin
from app.core.config import get_settings
from app.core.time import utc_now
from app.db.mongodb import get_database
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import AnalyticsDashboardResponse, AnalyticsSummaryResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/admin/analytics", tags=["admin analytics"])
logger = logging.getLogger(__name__)


MAX_QUERY_RANGE_DAYS = 365


def get_analytics_service(
    database: Annotated[AsyncDatabase[Any], Depends(get_database)],
) -> AnalyticsService:
    return AnalyticsService(
        analytics_repository=AnalyticsRepository(database),
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _resolve_dashboard_period(
    *,
    days: int,
    date_from: datetime | None,
    date_to: datetime | None,
) -> tuple[datetime, datetime]:
    retention_days = max(
        1,
        min(get_settings().analytics_raw_event_ttl_days, MAX_QUERY_RANGE_DAYS),
    )
    if (date_from is None) != (date_to is None):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="date_from and date_to must be provided together",
        )

    if date_from is not None and date_to is not None:
        normalized_from = _as_utc(date_from)
        normalized_to = _as_utc(date_to)

        if normalized_from >= normalized_to:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="date_from must be earlier than date_to",
            )

        if normalized_to - normalized_from > timedelta(days=retention_days):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    "analytics date range cannot exceed raw event retention: "
                    f"{retention_days} days"
                ),
            )

        return normalized_from, normalized_to

    if days > retention_days:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                "analytics date range cannot exceed raw event retention: "
                f"{retention_days} days"
            ),
        )

    today_start = datetime.combine(utc_now().date(), time.min, tzinfo=UTC)
    return (
        today_start - timedelta(days=days - 1),
        today_start + timedelta(days=1),
    )


@router.get(
    "/dashboard",
    response_model=AnalyticsDashboardResponse,
    include_in_schema=False,
)
async def analytics_dashboard(
    _current_admin: Annotated[dict, Depends(require_admin)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    days: Annotated[int, Query(ge=1, le=365)] = 30,
    date_from: Annotated[datetime | None, Query()] = None,
    date_to: Annotated[datetime | None, Query()] = None,
) -> AnalyticsDashboardResponse:
    resolved_from, resolved_to = _resolve_dashboard_period(
        days=days,
        date_from=date_from,
        date_to=date_to,
    )
    try:
        return await service.dashboard(
            date_from=resolved_from,
            date_to=resolved_to,
        )
    except Exception as exc:
        logger.exception("Could not build admin analytics dashboard")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analytics dashboard is temporarily unavailable",
        ) from exc


@router.get(
    "/summary",
    response_model=AnalyticsSummaryResponse,
    include_in_schema=False,
)
async def analytics_summary(
    _current_admin: Annotated[dict, Depends(require_admin)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> AnalyticsSummaryResponse:
    return await service.summary()
