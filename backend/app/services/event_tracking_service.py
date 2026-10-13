import json
import logging
import re
from enum import Enum
from typing import Any

from app.core.enums import AnalyticsEventSource, AnalyticsEventType
from app.repositories.analytics_repository import AnalyticsRepository

logger = logging.getLogger(__name__)

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


def _sanitize_value(value: Any, depth: int = 0) -> Any:
    if depth > 4:
        return "[truncated]"

    if value is None or isinstance(value, bool | int | float):
        return value

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, str):
        return value[:240]

    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in list(value.items())[:30]:
            if _is_forbidden_metadata_key(key):
                continue
            result[str(key)[:80]] = _sanitize_value(item, depth + 1)
        return result

    if isinstance(value, list | tuple | set):
        return [_sanitize_value(item, depth + 1) for item in list(value)[:30]]

    return str(value)[:240]


def _sanitize_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    sanitized = _sanitize_value(metadata or {})
    result = sanitized if isinstance(sanitized, dict) else {}
    rendered = json.dumps(result, ensure_ascii=False, separators=(",", ":"))

    if len(rendered.encode("utf-8")) <= 4096:
        return result

    return {
        "metadata_truncated": True,
        "retained_keys": list(result)[:20],
    }


class EventTrackingService:
    """Best-effort server-owned analytics.

    Analytics failures are logged but never break registration, recommendations,
    feedback, replacements, profile updates, or LLM fallback behavior.
    """

    def __init__(self, analytics_repository: AnalyticsRepository) -> None:
        self.analytics_repository = analytics_repository

    async def record(
        self,
        event_type: AnalyticsEventType,
        *,
        anonymous_id: str | None = None,
        user_id: str | None = None,
        recommendation_id: str | None = None,
        product_external_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        try:
            return await self.analytics_repository.save_event(
                event_type=event_type.value,
                event_source=AnalyticsEventSource.SERVER.value,
                anonymous_id=anonymous_id,
                user_id=user_id,
                recommendation_id=recommendation_id,
                product_external_id=product_external_id,
                metadata=_sanitize_metadata(metadata),
            )
        except Exception:
            logger.exception(
                "Could not record server analytics event %s",
                event_type.value,
            )
            return None
