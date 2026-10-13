import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient

from app.api.v1.endpoints.admin_analytics import get_analytics_service
from app.core.config import get_settings
from app.main import app


def _database() -> tuple[MongoClient, Any]:
    settings = get_settings()
    client = MongoClient(
        settings.mongo_uri,
        uuidRepresentation="standard",
        serverSelectionTimeoutMS=5000,
    )
    return client, client[settings.mongo_db_name]


def _register(client: TestClient) -> tuple[str, dict]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"dashboard-admin-{uuid4().hex}@example.com",
            "password": "StrongPassword123!",
            "full_name": "Dashboard Admin",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    return payload["access_token"], payload["user"]


def _set_role(email: str, role: str) -> None:
    mongo_client, database = _database()
    try:
        result = database["users"].update_one(
            {"email": email.lower()},
            {"$set": {"role": role}},
        )
        assert result.matched_count == 1
    finally:
        mongo_client.close()


def _admin_headers(client: TestClient) -> dict[str, str]:
    token, user = _register(client)
    _set_role(user["email"], "admin")
    return {"Authorization": f"Bearer {token}"}


def _future_window() -> tuple[datetime, datetime]:
    offset = int(uuid4().hex[:8], 16) % 4000
    date_from = datetime(2040, 1, 1, tzinfo=UTC) + timedelta(days=offset)
    return date_from, date_from + timedelta(days=2)


def _period_params(date_from: datetime, date_to: datetime) -> dict[str, str]:
    return {
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
    }


def _routine_item(product_external_id: str) -> dict[str, Any]:
    return {
        "product": {"external_id": product_external_id},
    }


@contextmanager
def _seed_dashboard_data() -> Iterator[dict[str, Any]]:
    marker = f"dashboard-{uuid4().hex}"
    date_from, date_to = _future_window()
    first_day = date_from + timedelta(hours=6)
    second_day = date_from + timedelta(days=1, hours=6)
    outside = date_from - timedelta(days=2)

    product_1 = f"dashboard-product-1-{uuid4().hex}"
    product_2 = f"dashboard-product-2-{uuid4().hex}"
    product_3 = f"dashboard-product-3-{uuid4().hex}"

    mongo_client, database = _database()
    try:
        database["products"].insert_many(
            [
                {
                    "external_id": product_1,
                    "name": "Dashboard Cleanser",
                    "brand": "Dashboard Brand A",
                    "dashboard_test_marker": marker,
                },
                {
                    "external_id": product_2,
                    "name": "Dashboard Serum",
                    "brand": "Dashboard Brand B",
                    "dashboard_test_marker": marker,
                },
                {
                    "external_id": product_3,
                    "name": "Dashboard SPF",
                    "brand": "Dashboard Brand C",
                    "dashboard_test_marker": marker,
                },
            ]
        )

        database["users"].insert_many(
            [
                {
                    "email": f"private-{uuid4().hex}@example.com",
                    "password_hash": "private-password-hash",
                    "full_name": "Private Dashboard User",
                    "anonymous_id": "private-anonymous-id",
                    "role": "user",
                    "is_active": True,
                    "created_at": first_day,
                    "updated_at": first_day,
                    "last_seen_at": first_day,
                    "dashboard_test_marker": marker,
                },
                {
                    "email": f"private-{uuid4().hex}@example.com",
                    "password_hash": "private-password-hash",
                    "full_name": "Private Dashboard User",
                    "anonymous_id": "private-anonymous-id",
                    "role": "user",
                    "is_active": True,
                    "created_at": second_day,
                    "updated_at": second_day,
                    "last_seen_at": second_day,
                    "dashboard_test_marker": marker,
                },
                {
                    "email": f"outside-{uuid4().hex}@example.com",
                    "created_at": outside,
                    "updated_at": outside,
                    "last_seen_at": first_day,
                    "dashboard_test_marker": marker,
                },
            ]
        )

        database["analytics_events"].insert_many(
            [
                *[
                    {
                        "event_type": "questionnaire_completed",
                        "event_source": "server",
                        "metadata": {"secret_token": "must-not-leak"},
                        "created_at": timestamp,
                        "dashboard_test_marker": marker,
                    }
                    for timestamp in (first_day, second_day)
                ],
                *[
                    {
                        "event_type": "llm_explanation_success",
                        "event_source": "server",
                        "metadata": {"system_prompt": "must-not-leak"},
                        "created_at": timestamp,
                        "dashboard_test_marker": marker,
                    }
                    for timestamp in (first_day, first_day, second_day)
                ],
                {
                    "event_type": "llm_explanation_fallback",
                    "event_source": "server",
                    "metadata": {"user_prompt": "must-not-leak"},
                    "created_at": second_day,
                    "dashboard_test_marker": marker,
                },
                {
                    "event_type": "product_viewed",
                    "event_source": "public",
                    "anonymous_id": "private-anonymous-id",
                    "product_external_id": product_1,
                    "created_at": first_day,
                    "dashboard_test_marker": marker,
                },
                {
                    "event_type": "favorite_added",
                    "event_source": "public",
                    "anonymous_id": "private-anonymous-id",
                    "product_external_id": product_2,
                    "created_at": first_day,
                    "dashboard_test_marker": marker,
                },
                {
                    "event_type": "cosmetic_bag_added",
                    "event_source": "public",
                    "anonymous_id": "private-anonymous-id",
                    "product_external_id": product_2,
                    "created_at": second_day,
                    "dashboard_test_marker": marker,
                },
                {
                    "event_type": "store_opened",
                    "event_source": "public",
                    "anonymous_id": "private-anonymous-id",
                    "product_external_id": product_1,
                    "created_at": second_day,
                    "dashboard_test_marker": marker,
                },
                {
                    "event_type": "product_viewed",
                    "event_source": "public",
                    "created_at": outside,
                    "dashboard_test_marker": marker,
                },
            ]
        )

        database["recommendation_sessions"].insert_many(
            [
                {
                    "request": {
                        "skin_type": "combination",
                        "concerns": ["acne", "sebum"],
                        "budget": "balanced",
                        "excluded_ingredients": ["fragrance"],
                        "custom_restrictions": [
                            "private-medical-custom-restriction"
                        ],
                        "experience": "beginner",
                        "anonymous_id": "private-anonymous-id",
                    },
                    "result": {
                        "routine": {
                            "morning": [_routine_item(product_1)],
                            "evening": [
                                _routine_item(product_1),
                                _routine_item(product_2),
                            ],
                        }
                    },
                    "user_id": "private-user-id",
                    "anonymous_id": "private-anonymous-id",
                    "created_at": first_day,
                    "dashboard_test_marker": marker,
                },
                {
                    "request": {
                        "skin_type": "dry",
                        "concerns": ["dryness"],
                        "budget": "minimum",
                        "excluded_ingredients": ["alcohol"],
                        "custom_restrictions": [],
                        "experience": "guided",
                    },
                    "result": {
                        "routine": {
                            "morning": [
                                _routine_item(product_1),
                                _routine_item(product_3),
                            ],
                            "evening": [],
                        }
                    },
                    "created_at": second_day,
                    "dashboard_test_marker": marker,
                },
                {
                    "request": {
                        "skin_type": "sensitive",
                        "concerns": ["reactivity"],
                        "budget": "premium",
                        "excluded_ingredients": ["essential_oils"],
                        "custom_restrictions": [],
                        "experience": "advanced",
                    },
                    "result": {
                        "routine": {
                            "morning": [_routine_item(product_3)],
                            "evening": [],
                        }
                    },
                    "created_at": outside,
                    "dashboard_test_marker": marker,
                },
            ]
        )

        database["feedback_events"].insert_many(
            [
                {
                    "recommendation_id": "private-recommendation-id",
                    "product_external_id": product_1,
                    "reason": "too_expensive",
                    "comment": "private feedback comment",
                    "anonymous_id": "private-anonymous-id",
                    "created_at": first_day,
                    "dashboard_test_marker": marker,
                },
                {
                    "recommendation_id": "private-recommendation-id",
                    "product_external_id": product_1,
                    "reason": "dislikes_brand",
                    "comment": "private feedback comment",
                    "anonymous_id": "private-anonymous-id",
                    "created_at": second_day,
                    "dashboard_test_marker": marker,
                },
                {
                    "product_external_id": product_3,
                    "reason": "other",
                    "comment": "outside private comment",
                    "created_at": outside,
                    "dashboard_test_marker": marker,
                },
            ]
        )

        database["replacement_sessions"].insert_many(
            [
                {
                    "recommendation_id": "private-recommendation-id",
                    "feedback_id": "private-feedback-id",
                    "original_product_external_id": product_1,
                    "selected_product_external_id": product_2,
                    "reason": "too_expensive",
                    "created_at": first_day,
                    "updated_at": first_day,
                    "dashboard_test_marker": marker,
                },
                {
                    "recommendation_id": "private-recommendation-id",
                    "feedback_id": "private-feedback-id",
                    "original_product_external_id": product_1,
                    "selected_product_external_id": None,
                    "reason": "dislikes_brand",
                    "created_at": second_day,
                    "updated_at": second_day,
                    "dashboard_test_marker": marker,
                },
                {
                    "original_product_external_id": product_3,
                    "selected_product_external_id": product_1,
                    "reason": "other",
                    "created_at": outside,
                    "updated_at": outside,
                    "dashboard_test_marker": marker,
                },
            ]
        )

        yield {
            "date_from": date_from,
            "date_to": date_to,
            "product_1": product_1,
            "product_2": product_2,
            "product_3": product_3,
        }
    finally:
        for collection_name in (
            "products",
            "users",
            "analytics_events",
            "recommendation_sessions",
            "feedback_events",
            "replacement_sessions",
        ):
            database[collection_name].delete_many(
                {"dashboard_test_marker": marker}
            )
        mongo_client.close()


def _sum_activity(payload: dict[str, Any], metric: str) -> int:
    return sum(int(point[metric]) for point in payload["activity"])


def _assert_no_sensitive_keys(value: Any) -> None:
    forbidden_parts = {
        "anonymous_id",
        "authorization",
        "comment",
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

    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).casefold()
            assert not any(part in normalized for part in forbidden_parts)
            _assert_no_sensitive_keys(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_sensitive_keys(item)


def test_admin_dashboard_without_token_returns_401() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/admin/analytics/dashboard")

    assert response.status_code == 401


def test_admin_dashboard_for_regular_user_returns_403() -> None:
    with TestClient(app) as client:
        token, _ = _register(client)
        response = client.get(
            "/api/v1/admin/analytics/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_admin_dashboard_is_hidden_from_openapi() -> None:
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    assert "/api/v1/admin/analytics/dashboard" not in schema["paths"]


@pytest.mark.parametrize(
    "params",
    [
        {"date_from": "2040-01-01T00:00:00Z"},
        {
            "date_from": "2040-01-02T00:00:00Z",
            "date_to": "2040-01-01T00:00:00Z",
        },
        {"days": "0"},
        {"days": "366"},
    ],
)
def test_admin_dashboard_validates_date_filters(params: dict[str, str]) -> None:
    with TestClient(app) as client:
        headers = _admin_headers(client)
        response = client.get(
            "/api/v1/admin/analytics/dashboard",
            headers=headers,
            params=params,
        )

    assert response.status_code == 422


def test_admin_dashboard_empty_range_returns_zero_metrics() -> None:
    date_from, date_to = _future_window()

    with TestClient(app) as client:
        headers = _admin_headers(client)
        response = client.get(
            "/api/v1/admin/analytics/dashboard",
            headers=headers,
            params=_period_params(date_from, date_to),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["period"]["calendar_days"] == 2
    assert all(value == 0 for value in payload["overview"].values())
    assert payload["conversion"]["llm_fallback_rate"]["rate_percent"] == 0.0
    assert len(payload["activity"]) == 2
    assert all(
        sum(value for key, value in point.items() if key != "date") == 0
        for point in payload["activity"]
    )
    assert payload["products"]["top_recommended"] == []
    assert payload["feedback"]["reasons_by_product"] == []
    assert payload["audience"]["skin_types"] == {}
    assert payload["users"]["registered_in_period"] == 0
    assert payload["users"]["unique_visitors"] == 0


def test_admin_dashboard_returns_trusted_aggregates_without_pii() -> None:
    with _seed_dashboard_data() as seeded:
        with TestClient(app) as client:
            headers = _admin_headers(client)
            response = client.get(
                "/api/v1/admin/analytics/dashboard",
                headers=headers,
                params=_period_params(
                    seeded["date_from"],
                    seeded["date_to"],
                ),
            )

    assert response.status_code == 200
    payload = response.json()
    overview = payload["overview"]

    assert overview == {
        "registrations": 2,
        "questionnaires_completed": 2,
        "recommendations_generated": 2,
        "feedback_submitted": 2,
        "replacement_sessions": 2,
        "replacement_selections": 1,
        "recommendation_shares": 0,
        "llm_success": 3,
        "llm_fallback": 1,
        "public_events": 4,
        "server_events": 6,
    }

    assert payload["users"]["registered_total"] >= 3
    assert payload["users"]["registered_in_period"] == 2
    assert payload["users"]["active_accounts"] == 3
    assert payload["users"]["returning_accounts"] == 1
    assert payload["users"]["unique_visitors"] == 1
    assert payload["users"]["anonymous_visitors"] == 1
    assert payload["llm"]["attempts"] == 4
    assert payload["llm"]["success"] == 3
    assert payload["llm"]["fallback"] == 1
    assert payload["llm"]["success_rate"]["rate_percent"] == 75.0

    assert payload["conversion"]["questionnaire_to_recommendation"] == {
        "numerator": 2,
        "denominator": 2,
        "rate_percent": 100.0,
    }
    assert payload["conversion"]["feedback_to_replacement"][
        "rate_percent"
    ] == 100.0
    assert payload["conversion"]["replacement_to_selection"][
        "rate_percent"
    ] == 50.0
    assert payload["conversion"]["llm_fallback_rate"] == {
        "numerator": 1,
        "denominator": 4,
        "rate_percent": 25.0,
    }

    assert payload["period"]["timezone"] == "UTC"
    assert payload["period"]["calendar_days"] == 2
    for metric, expected in overview.items():
        assert _sum_activity(payload, metric) == expected

    top_recommended = payload["products"]["top_recommended"]
    assert top_recommended[0]["product_external_id"] == seeded["product_1"]
    assert top_recommended[0]["name"] == "Dashboard Cleanser"
    assert top_recommended[0]["count"] == 2

    assert payload["products"]["top_viewed"][0]["product_external_id"] == seeded[
        "product_1"
    ]
    assert payload["products"]["top_favorited"][0]["product_external_id"] == seeded[
        "product_2"
    ]
    assert payload["products"]["top_bagged"][0]["product_external_id"] == seeded[
        "product_2"
    ]
    assert payload["products"]["top_store_opened"][0][
        "product_external_id"
    ] == seeded["product_1"]

    negative_feedback = payload["products"]["most_negative_feedback"]
    assert negative_feedback[0]["product_external_id"] == seeded["product_1"]
    assert negative_feedback[0]["count"] == 2

    replacement_frequency = payload["products"]["replacement_frequency"]
    assert replacement_frequency[0]["product_external_id"] == seeded["product_1"]
    assert replacement_frequency[0]["count"] == 2

    selected_frequency = payload["products"][
        "replacement_selection_frequency"
    ]
    assert selected_frequency == [
        {
            "product_external_id": seeded["product_2"],
            "name": "Dashboard Serum",
            "brand": "Dashboard Brand B",
            "count": 1,
        }
    ]

    assert payload["feedback"]["reasons"] == {
        "dislikes_brand": 1,
        "too_expensive": 1,
    }
    assert payload["feedback"]["reasons_by_product"][0]["reasons"] == {
        "dislikes_brand": 1,
        "too_expensive": 1,
    }
    assert payload["replacements"]["reasons"] == {
        "dislikes_brand": 1,
        "too_expensive": 1,
    }

    assert payload["audience"] == {
        "skin_types": {"combination": 1, "dry": 1},
        "concerns": {"acne": 1, "dryness": 1, "sebum": 1},
        "restrictions": {"alcohol": 1, "custom": 1, "fragrance": 1},
        "budgets": {"balanced": 1, "minimum": 1},
        "experience": {"beginner": 1, "guided": 1},
    }

    _assert_no_sensitive_keys(payload)
    rendered = json.dumps(payload, ensure_ascii=False).casefold()
    for sensitive_value in (
        "private dashboard user",
        "private feedback comment",
        "private-medical-custom-restriction",
        "private-anonymous-id",
        "private-user-id",
        "must-not-leak",
    ):
        assert sensitive_value not in rendered


def test_admin_dashboard_failure_returns_generic_503() -> None:
    class FailingDashboardService:
        async def dashboard(self, **_: Any) -> None:
            raise RuntimeError("private database stack trace")

    with TestClient(app, raise_server_exceptions=False) as client:
        headers = _admin_headers(client)
        app.dependency_overrides[get_analytics_service] = (
            lambda: FailingDashboardService()
        )
        try:
            response = client.get(
                "/api/v1/admin/analytics/dashboard",
                headers=headers,
            )
        finally:
            app.dependency_overrides.pop(get_analytics_service, None)

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Analytics dashboard is temporarily unavailable"
    }
    assert "private database stack trace" not in response.text.casefold()


def test_legacy_admin_summary_recent_events_are_anonymized() -> None:
    with TestClient(app) as client:
        headers = _admin_headers(client)
        public_response = client.post(
            "/api/v1/analytics/events",
            json={
                "event_type": "product_viewed",
                "anonymous_id": "summary-private-anonymous-id",
                "recommendation_id": "summary-private-recommendation-id",
                "product_external_id": "summary-product",
                "metadata": {"source": "summary-test"},
            },
        )
        assert public_response.status_code == 201

        response = client.get(
            "/api/v1/admin/analytics/summary",
            headers=headers,
        )

    assert response.status_code == 200
    recent_events = response.json()["recent_events"]
    assert recent_events
    allowed_keys = {
        "event_type",
        "event_source",
        "product_external_id",
        "created_at",
    }
    assert all(set(event) <= allowed_keys for event in recent_events)
