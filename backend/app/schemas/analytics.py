import json
import re
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import PublicAnalyticsEventType

_FORBIDDEN_METADATA_KEY_PARTS = {
    "anonymous_id",
    "api_key",
    "authorization",
    "comment",
    "cookie",
    "credential",
    "email",
    "full_name",
    "password",
    "phone",
    "prompt",
    "secret",
    "token",
    "user_id",
}


def _normalized_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).casefold()).strip("_")


def _is_forbidden_metadata_key(value: Any) -> bool:
    normalized = _normalized_key(value)
    compact = normalized.replace("_", "")
    return any(
        part in normalized or part.replace("_", "") in compact
        for part in _FORBIDDEN_METADATA_KEY_PARTS
    )


def _forbidden_metadata_keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        result: list[str] = []
        for key, item in value.items():
            if _is_forbidden_metadata_key(key):
                result.append(str(key))
            result.extend(_forbidden_metadata_keys(item))
        return result

    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(_forbidden_metadata_keys(item))
        return result

    return []


class AnalyticsEventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: PublicAnalyticsEventType
    anonymous_id: str | None = Field(default=None, max_length=120)
    recommendation_id: str | None = Field(default=None, max_length=120)
    product_external_id: str | None = Field(default=None, max_length=120)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        if len(value) > 30:
            raise ValueError("metadata contains too many top-level fields")

        forbidden = sorted(set(_forbidden_metadata_keys(value)))
        if forbidden:
            raise ValueError(
                "metadata contains forbidden fields: " + ", ".join(forbidden)
            )

        encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        if len(encoded.encode("utf-8")) > 4096:
            raise ValueError("metadata is larger than 4096 bytes")

        return value


class AnalyticsEventResponse(BaseModel):
    event_id: str
    status: str = "recorded"
    created_at: datetime


class AnalyticsSummaryResponse(BaseModel):
    total_events: int
    events_by_type: dict[str, int]
    top_products: list[dict[str, Any]]
    feedback_reasons: dict[str, int]
    recent_events: list[dict[str, Any]]


class AnalyticsDashboardPeriod(BaseModel):
    date_from: datetime
    date_to: datetime
    timezone: Literal["UTC"] = "UTC"
    calendar_days: int = Field(ge=1)


class AnalyticsDashboardOverview(BaseModel):
    registrations: int = Field(ge=0)
    questionnaires_completed: int = Field(ge=0)
    recommendations_generated: int = Field(ge=0)
    feedback_submitted: int = Field(ge=0)
    replacement_sessions: int = Field(ge=0)
    replacement_selections: int = Field(ge=0)
    recommendation_shares: int = Field(ge=0)
    llm_success: int = Field(ge=0)
    llm_fallback: int = Field(ge=0)
    public_events: int = Field(ge=0)
    server_events: int = Field(ge=0)


class AnalyticsDashboardUsers(BaseModel):
    registered_total: int = Field(ge=0)
    registered_in_period: int = Field(ge=0)
    active_accounts: int = Field(ge=0)
    returning_accounts: int = Field(ge=0)
    unique_visitors: int = Field(ge=0)
    anonymous_visitors: int = Field(ge=0)


class AnalyticsRate(BaseModel):
    numerator: int = Field(ge=0)
    denominator: int = Field(ge=0)
    rate_percent: float = Field(ge=0)


class AnalyticsDashboardLLM(BaseModel):
    enabled: bool
    configured: bool
    provider: str
    model: str
    attempts: int = Field(ge=0)
    success: int = Field(ge=0)
    fallback: int = Field(ge=0)
    success_rate: AnalyticsRate


class AnalyticsDashboardConversion(BaseModel):
    questionnaire_to_recommendation: AnalyticsRate
    feedback_to_replacement: AnalyticsRate
    replacement_to_selection: AnalyticsRate
    llm_fallback_rate: AnalyticsRate


class AnalyticsActivityPoint(BaseModel):
    date: date
    registrations: int = Field(ge=0)
    questionnaires_completed: int = Field(ge=0)
    recommendations_generated: int = Field(ge=0)
    feedback_submitted: int = Field(ge=0)
    replacement_sessions: int = Field(ge=0)
    replacement_selections: int = Field(ge=0)
    recommendation_shares: int = Field(ge=0)
    llm_success: int = Field(ge=0)
    llm_fallback: int = Field(ge=0)
    public_events: int = Field(ge=0)
    server_events: int = Field(ge=0)


class AnalyticsProductCount(BaseModel):
    product_external_id: str
    name: str | None = None
    brand: str | None = None
    count: int = Field(ge=0)


class AnalyticsProductFeedbackBreakdown(BaseModel):
    product_external_id: str
    name: str | None = None
    brand: str | None = None
    count: int = Field(ge=0)
    reasons: dict[str, int] = Field(default_factory=dict)


class AnalyticsDashboardProducts(BaseModel):
    top_recommended: list[AnalyticsProductCount] = Field(default_factory=list)
    top_viewed: list[AnalyticsProductCount] = Field(default_factory=list)
    top_favorited: list[AnalyticsProductCount] = Field(default_factory=list)
    top_bagged: list[AnalyticsProductCount] = Field(default_factory=list)
    top_store_opened: list[AnalyticsProductCount] = Field(default_factory=list)
    most_negative_feedback: list[AnalyticsProductCount] = Field(default_factory=list)
    replacement_frequency: list[AnalyticsProductCount] = Field(default_factory=list)
    replacement_selection_frequency: list[AnalyticsProductCount] = Field(
        default_factory=list
    )


class AnalyticsDashboardFeedback(BaseModel):
    total: int = Field(ge=0)
    reasons: dict[str, int] = Field(default_factory=dict)
    reasons_by_product: list[AnalyticsProductFeedbackBreakdown] = Field(
        default_factory=list
    )


class AnalyticsDashboardReplacements(BaseModel):
    generated: int = Field(ge=0)
    selected: int = Field(ge=0)
    selection_rate: AnalyticsRate
    reasons: dict[str, int] = Field(default_factory=dict)


class AnalyticsDashboardAudience(BaseModel):
    skin_types: dict[str, int] = Field(default_factory=dict)
    concerns: dict[str, int] = Field(default_factory=dict)
    restrictions: dict[str, int] = Field(default_factory=dict)
    budgets: dict[str, int] = Field(default_factory=dict)
    experience: dict[str, int] = Field(default_factory=dict)


class AnalyticsDashboardResponse(BaseModel):
    period: AnalyticsDashboardPeriod
    overview: AnalyticsDashboardOverview
    users: AnalyticsDashboardUsers
    llm: AnalyticsDashboardLLM
    conversion: AnalyticsDashboardConversion
    activity: list[AnalyticsActivityPoint] = Field(default_factory=list)
    products: AnalyticsDashboardProducts
    feedback: AnalyticsDashboardFeedback
    replacements: AnalyticsDashboardReplacements
    audience: AnalyticsDashboardAudience
