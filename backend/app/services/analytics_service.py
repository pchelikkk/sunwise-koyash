from asyncio import gather
from datetime import date, datetime, timedelta

from app.core.config import get_settings
from app.core.enums import AnalyticsEventSource, AnalyticsEventType
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import (
    AnalyticsActivityPoint,
    AnalyticsDashboardAudience,
    AnalyticsDashboardConversion,
    AnalyticsDashboardFeedback,
    AnalyticsDashboardLLM,
    AnalyticsDashboardOverview,
    AnalyticsDashboardPeriod,
    AnalyticsDashboardProducts,
    AnalyticsDashboardReplacements,
    AnalyticsDashboardResponse,
    AnalyticsDashboardUsers,
    AnalyticsEventCreate,
    AnalyticsEventResponse,
    AnalyticsProductCount,
    AnalyticsProductFeedbackBreakdown,
    AnalyticsRate,
    AnalyticsSummaryResponse,
)


class AnalyticsService:
    def __init__(self, analytics_repository: AnalyticsRepository) -> None:
        self.analytics_repository = analytics_repository

    async def record_public_event(
        self,
        payload: AnalyticsEventCreate,
        *,
        authenticated_user_id: str | None,
    ) -> AnalyticsEventResponse:
        document = await self.analytics_repository.save_event(
            event_type=payload.event_type.value,
            event_source=AnalyticsEventSource.PUBLIC.value,
            anonymous_id=payload.anonymous_id,
            user_id=authenticated_user_id,
            recommendation_id=payload.recommendation_id,
            product_external_id=payload.product_external_id,
            metadata=payload.metadata,
        )

        return AnalyticsEventResponse(
            event_id=document["event_id"],
            created_at=document["created_at"],
        )

    async def summary(self) -> AnalyticsSummaryResponse:
        total_events = await self.analytics_repository.count_events()
        events_by_type = await self.analytics_repository.count_by_event_type()
        top_products = await self.analytics_repository.top_products()
        feedback_reasons = await self.analytics_repository.feedback_reasons()
        recent_events = await self.analytics_repository.recent_events()

        return AnalyticsSummaryResponse(
            total_events=total_events,
            events_by_type=events_by_type,
            top_products=top_products,
            feedback_reasons=feedback_reasons,
            recent_events=recent_events,
        )

    async def dashboard(
        self,
        *,
        date_from: datetime,
        date_to: datetime,
    ) -> AnalyticsDashboardResponse:
        (
            overview_data,
            users_data,
            activity_data,
            top_recommended,
            top_viewed,
            top_favorited,
            top_bagged,
            top_store_opened,
            most_negative_feedback,
            replacement_frequency,
            replacement_selection_frequency,
            feedback_reasons,
            feedback_by_product,
            replacement_reasons,
            audience_data,
        ) = await gather(
            self.analytics_repository.dashboard_overview(date_from, date_to),
            self.analytics_repository.dashboard_users(date_from, date_to),
            self.analytics_repository.dashboard_activity(date_from, date_to),
            self.analytics_repository.dashboard_top_recommended_products(
                date_from,
                date_to,
            ),
            self.analytics_repository.dashboard_event_product_counts(
                [
                    AnalyticsEventType.PRODUCT_DETAILS_OPENED.value,
                    "product_viewed",
                ],
                date_from,
                date_to,
            ),
            self.analytics_repository.dashboard_event_product_counts(
                [AnalyticsEventType.FAVORITE_ADDED.value],
                date_from,
                date_to,
            ),
            self.analytics_repository.dashboard_event_product_counts(
                [AnalyticsEventType.COSMETIC_BAG_ADDED.value],
                date_from,
                date_to,
            ),
            self.analytics_repository.dashboard_event_product_counts(
                [AnalyticsEventType.STORE_OPENED.value],
                date_from,
                date_to,
            ),
            self.analytics_repository.dashboard_product_counts(
                "feedback_events",
                "product_external_id",
                date_from,
                date_to,
            ),
            self.analytics_repository.dashboard_product_counts(
                "replacement_sessions",
                "original_product_external_id",
                date_from,
                date_to,
            ),
            self.analytics_repository.dashboard_product_counts(
                "replacement_sessions",
                "selected_product_external_id",
                date_from,
                date_to,
            ),
            self.analytics_repository.dashboard_feedback_reasons(
                date_from,
                date_to,
            ),
            self.analytics_repository.dashboard_feedback_reasons_by_product(
                date_from,
                date_to,
            ),
            self.analytics_repository.dashboard_replacement_reasons(
                date_from,
                date_to,
            ),
            self.analytics_repository.dashboard_audience(date_from, date_to),
        )

        product_ids = {
            item["product_external_id"]
            for collection in (
                top_recommended,
                top_viewed,
                top_favorited,
                top_bagged,
                top_store_opened,
                most_negative_feedback,
                replacement_frequency,
                replacement_selection_frequency,
                feedback_by_product,
            )
            for item in collection
        }
        product_labels = await self.analytics_repository.product_labels(product_ids)

        overview = AnalyticsDashboardOverview(**overview_data)
        settings = get_settings()
        llm_provider = settings.llm_provider.casefold()
        if llm_provider == "openai":
            llm_key = settings.openai_api_key
            llm_model = settings.openai_model
        else:
            llm_key = settings.vsellm_api_key
            llm_model = settings.vsellm_model
        replacement_selection_rate = self._rate(
            overview.replacement_selections,
            overview.replacement_sessions,
        )

        activity = self._build_activity(
            date_from=date_from,
            date_to=date_to,
            activity_data=activity_data,
        )

        return AnalyticsDashboardResponse(
            period=AnalyticsDashboardPeriod(
                date_from=date_from,
                date_to=date_to,
                calendar_days=len(activity),
            ),
            overview=overview,
            users=AnalyticsDashboardUsers(**users_data),
            llm=AnalyticsDashboardLLM(
                enabled=settings.llm_enabled,
                configured=bool(
                    settings.llm_enabled
                    and llm_provider in {"openai", "vsellm"}
                    and llm_key
                ),
                provider=llm_provider,
                model=llm_model,
                attempts=overview.llm_success + overview.llm_fallback,
                success=overview.llm_success,
                fallback=overview.llm_fallback,
                success_rate=self._rate(
                    overview.llm_success,
                    overview.llm_success + overview.llm_fallback,
                ),
            ),
            conversion=AnalyticsDashboardConversion(
                questionnaire_to_recommendation=self._rate(
                    overview.recommendations_generated,
                    overview.questionnaires_completed,
                ),
                feedback_to_replacement=self._rate(
                    overview.replacement_sessions,
                    overview.feedback_submitted,
                ),
                replacement_to_selection=replacement_selection_rate,
                llm_fallback_rate=self._rate(
                    overview.llm_fallback,
                    overview.llm_success + overview.llm_fallback,
                ),
            ),
            activity=activity,
            products=AnalyticsDashboardProducts(
                top_recommended=self._enrich_product_counts(
                    top_recommended,
                    product_labels,
                ),
                top_viewed=self._enrich_product_counts(
                    top_viewed,
                    product_labels,
                ),
                top_favorited=self._enrich_product_counts(
                    top_favorited,
                    product_labels,
                ),
                top_bagged=self._enrich_product_counts(
                    top_bagged,
                    product_labels,
                ),
                top_store_opened=self._enrich_product_counts(
                    top_store_opened,
                    product_labels,
                ),
                most_negative_feedback=self._enrich_product_counts(
                    most_negative_feedback,
                    product_labels,
                ),
                replacement_frequency=self._enrich_product_counts(
                    replacement_frequency,
                    product_labels,
                ),
                replacement_selection_frequency=self._enrich_product_counts(
                    replacement_selection_frequency,
                    product_labels,
                ),
            ),
            feedback=AnalyticsDashboardFeedback(
                total=overview.feedback_submitted,
                reasons=feedback_reasons,
                reasons_by_product=self._enrich_feedback_breakdown(
                    feedback_by_product,
                    product_labels,
                ),
            ),
            replacements=AnalyticsDashboardReplacements(
                generated=overview.replacement_sessions,
                selected=overview.replacement_selections,
                selection_rate=replacement_selection_rate,
                reasons=replacement_reasons,
            ),
            audience=AnalyticsDashboardAudience(**audience_data),
        )

    @staticmethod
    def _rate(numerator: int, denominator: int) -> AnalyticsRate:
        rate_percent = 0.0
        if denominator > 0:
            rate_percent = round((numerator / denominator) * 100, 2)

        return AnalyticsRate(
            numerator=numerator,
            denominator=denominator,
            rate_percent=rate_percent,
        )

    @staticmethod
    def _build_activity(
        *,
        date_from: datetime,
        date_to: datetime,
        activity_data: dict[str, dict[str, int]],
    ) -> list[AnalyticsActivityPoint]:
        last_included = (date_to - timedelta(microseconds=1)).date()
        current: date = date_from.date()
        result: list[AnalyticsActivityPoint] = []

        while current <= last_included:
            key = current.isoformat()
            result.append(
                AnalyticsActivityPoint(
                    date=current,
                    registrations=activity_data["registrations"].get(key, 0),
                    questionnaires_completed=activity_data[
                        "questionnaires_completed"
                    ].get(key, 0),
                    recommendations_generated=activity_data[
                        "recommendations_generated"
                    ].get(key, 0),
                    feedback_submitted=activity_data["feedback_submitted"].get(
                        key,
                        0,
                    ),
                    replacement_sessions=activity_data[
                        "replacement_sessions"
                    ].get(key, 0),
                    replacement_selections=activity_data[
                        "replacement_selections"
                    ].get(key, 0),
                    recommendation_shares=activity_data[
                        "recommendation_shares"
                    ].get(key, 0),
                    llm_success=activity_data["llm_success"].get(key, 0),
                    llm_fallback=activity_data["llm_fallback"].get(key, 0),
                    public_events=activity_data["public_events"].get(key, 0),
                    server_events=activity_data["server_events"].get(key, 0),
                )
            )
            current += timedelta(days=1)

        return result

    @staticmethod
    def _enrich_product_counts(
        items: list[dict],
        labels: dict[str, dict[str, str | None]],
    ) -> list[AnalyticsProductCount]:
        result: list[AnalyticsProductCount] = []
        for item in items:
            external_id = str(item["product_external_id"])
            label = labels.get(external_id, {})
            result.append(
                AnalyticsProductCount(
                    product_external_id=external_id,
                    name=label.get("name"),
                    brand=label.get("brand"),
                    count=int(item["count"]),
                )
            )
        return result

    @staticmethod
    def _enrich_feedback_breakdown(
        items: list[dict],
        labels: dict[str, dict[str, str | None]],
    ) -> list[AnalyticsProductFeedbackBreakdown]:
        result: list[AnalyticsProductFeedbackBreakdown] = []
        for item in items:
            external_id = str(item["product_external_id"])
            label = labels.get(external_id, {})
            result.append(
                AnalyticsProductFeedbackBreakdown(
                    product_external_id=external_id,
                    name=label.get("name"),
                    brand=label.get("brand"),
                    count=int(item["count"]),
                    reasons={
                        str(reason): int(count)
                        for reason, count in item.get("reasons", {}).items()
                    },
                )
            )
        return result
