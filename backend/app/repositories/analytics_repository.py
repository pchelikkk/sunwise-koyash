from datetime import datetime
from typing import Any

from bson import ObjectId
from pymongo import DESCENDING
from pymongo.asynchronous.database import AsyncDatabase

from app.core.enums import AnalyticsEventSource, AnalyticsEventType
from app.core.time import utc_now


class AnalyticsRepository:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.database = database
        self.collection = database["analytics_events"]

    async def save_event(
        self,
        event_type: str,
        anonymous_id: str | None,
        user_id: str | None,
        recommendation_id: str | None,
        product_external_id: str | None,
        metadata: dict[str, Any],
        event_source: str = AnalyticsEventSource.PUBLIC.value,
    ) -> dict[str, Any]:
        document = {
            "event_type": event_type,
            "event_source": event_source,
            "anonymous_id": anonymous_id,
            "user_id": user_id,
            "recommendation_id": recommendation_id,
            "product_external_id": product_external_id,
            "metadata": metadata,
            "created_at": utc_now(),
        }

        result = await self.collection.insert_one(document)

        return {
            "event_id": str(result.inserted_id),
            **document,
        }

    async def count_events(self) -> int:
        return await self.collection.count_documents({})

    async def count_by_event_type(self) -> dict[str, int]:
        cursor = await self.collection.aggregate(
            [
                {"$group": {"_id": "$event_type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
            ]
        )

        result: dict[str, int] = {}

        async for item in cursor:
            if item["_id"] is not None:
                result[str(item["_id"])] = int(item["count"])

        return result

    async def top_products(self, limit: int = 5) -> list[dict[str, Any]]:
        cursor = await self.collection.aggregate(
            [
                {"$match": {"product_external_id": {"$exists": True, "$ne": None}}},
                {"$group": {"_id": "$product_external_id", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": limit},
            ]
        )

        result: list[dict[str, Any]] = []

        async for item in cursor:
            result.append(
                {
                    "product_external_id": item["_id"],
                    "count": int(item["count"]),
                }
            )

        return result

    async def feedback_reasons(self) -> dict[str, int]:
        cursor = await self.database["feedback_events"].aggregate(
            [
                {"$group": {"_id": "$reason", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
            ]
        )

        result: dict[str, int] = {}

        async for item in cursor:
            if item["_id"] is not None:
                result[str(item["_id"])] = int(item["count"])

        return result

    async def recent_events(self, limit: int = 10) -> list[dict[str, Any]]:
        cursor = self.collection.find({}).sort("created_at", DESCENDING).limit(limit)

        result: list[dict[str, Any]] = []

        async for document in cursor:
            result.append(
                {
                    "event_type": document.get("event_type"),
                    "event_source": document.get(
                        "event_source",
                        AnalyticsEventSource.PUBLIC.value,
                    ),
                    "product_external_id": document.get("product_external_id"),
                    "created_at": document.get("created_at"),
                }
            )

        return result

    async def clear_event(self, event_id: str) -> bool:
        if not ObjectId.is_valid(event_id):
            return False

        result = await self.collection.delete_one({"_id": ObjectId(event_id)})
        return result.deleted_count == 1

    @staticmethod
    def _window_query(date_from: datetime, date_to: datetime) -> dict[str, Any]:
        return {"created_at": {"$gte": date_from, "$lt": date_to}}

    async def dashboard_users(
        self,
        date_from: datetime,
        date_to: datetime,
    ) -> dict[str, int]:
        account_query = {
            "role": {"$ne": "admin"},
            "is_active": {"$ne": False},
        }
        registered_in_period_query = {
            **account_query,
            "created_at": {"$gte": date_from, "$lt": date_to},
        }
        active_accounts_query = {
            **account_query,
            "last_seen_at": {"$gte": date_from, "$lt": date_to},
        }
        returning_accounts_query = {
            **account_query,
            "created_at": {"$lt": date_from},
            "last_seen_at": {"$gte": date_from, "$lt": date_to},
        }

        event_window = self._window_query(date_from, date_to)
        authenticated_ids = {
            str(value)
            for value in await self.collection.distinct("user_id", event_window)
            if value not in (None, "")
        }
        anonymous_ids = {
            str(value)
            for value in await self.collection.distinct(
                "anonymous_id",
                {
                    **event_window,
                    "$or": [
                        {"user_id": {"$exists": False}},
                        {"user_id": None},
                        {"user_id": ""},
                    ],
                },
            )
            if value not in (None, "")
        }

        users = self.database["users"]
        return {
            "registered_total": await users.count_documents(account_query),
            "registered_in_period": await users.count_documents(
                registered_in_period_query
            ),
            "active_accounts": await users.count_documents(active_accounts_query),
            "returning_accounts": await users.count_documents(
                returning_accounts_query
            ),
            "unique_visitors": len(authenticated_ids) + len(anonymous_ids),
            "anonymous_visitors": len(anonymous_ids),
        }

    async def dashboard_event_product_counts(
        self,
        event_types: list[str],
        date_from: datetime,
        date_to: datetime,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        cursor = await self.collection.aggregate(
            [
                {
                    "$match": {
                        **self._window_query(date_from, date_to),
                        "event_type": {"$in": event_types},
                        "product_external_id": {"$nin": [None, ""]},
                    }
                },
                {
                    "$group": {
                        "_id": "$product_external_id",
                        "count": {"$sum": 1},
                    }
                },
                {"$sort": {"count": -1, "_id": 1}},
                {"$limit": limit},
            ]
        )
        return [
            {
                "product_external_id": str(item["_id"]),
                "count": int(item["count"]),
            }
            async for item in cursor
        ]

    async def _count_in_window(
        self,
        collection_name: str,
        date_from: datetime,
        date_to: datetime,
        extra_query: dict[str, Any] | None = None,
    ) -> int:
        query = self._window_query(date_from, date_to)
        if extra_query:
            query.update(extra_query)
        return await self.database[collection_name].count_documents(query)

    async def _group_collection_by_day(
        self,
        collection_name: str,
        date_from: datetime,
        date_to: datetime,
        extra_query: dict[str, Any] | None = None,
    ) -> dict[str, int]:
        query = self._window_query(date_from, date_to)
        if extra_query:
            query.update(extra_query)

        cursor = await self.database[collection_name].aggregate(
            [
                {"$match": query},
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$created_at",
                                "timezone": "UTC",
                            }
                        },
                        "count": {"$sum": 1},
                    }
                },
                {"$sort": {"_id": 1}},
            ]
        )

        result: dict[str, int] = {}
        async for item in cursor:
            if item.get("_id") is not None:
                result[str(item["_id"])] = int(item["count"])
        return result

    async def _group_server_event_by_day(
        self,
        event_type: AnalyticsEventType,
        date_from: datetime,
        date_to: datetime,
    ) -> dict[str, int]:
        return await self._group_collection_by_day(
            "analytics_events",
            date_from,
            date_to,
            {
                "event_source": AnalyticsEventSource.SERVER.value,
                "event_type": event_type.value,
            },
        )

    async def _distribution(
        self,
        field: str,
        date_from: datetime,
        date_to: datetime,
        *,
        array: bool,
        limit: int = 20,
    ) -> dict[str, int]:
        projected_value: Any
        if array:
            projected_value = {
                "$setUnion": [
                    {"$ifNull": [f"${field}", []]},
                    [],
                ]
            }
        else:
            projected_value = {"$ifNull": [f"${field}", None]}

        pipeline: list[dict[str, Any]] = [
            {"$match": self._window_query(date_from, date_to)},
            {"$project": {"value": projected_value}},
        ]

        if array:
            pipeline.append({"$unwind": "$value"})

        pipeline.extend(
            [
                {"$match": {"value": {"$nin": [None, ""]}}},
                {"$group": {"_id": "$value", "count": {"$sum": 1}}},
                {"$sort": {"count": -1, "_id": 1}},
                {"$limit": limit},
            ]
        )

        cursor = await self.database["recommendation_sessions"].aggregate(pipeline)
        result: dict[str, int] = {}
        async for item in cursor:
            result[str(item["_id"])] = int(item["count"])
        return result

    async def dashboard_overview(
        self,
        date_from: datetime,
        date_to: datetime,
    ) -> dict[str, int]:
        server_event_cursor = await self.collection.aggregate(
            [
                {
                    "$match": {
                        **self._window_query(date_from, date_to),
                        "event_source": AnalyticsEventSource.SERVER.value,
                    }
                },
                {"$group": {"_id": "$event_type", "count": {"$sum": 1}}},
            ]
        )
        server_event_counts: dict[str, int] = {}
        async for item in server_event_cursor:
            if item.get("_id") is not None:
                server_event_counts[str(item["_id"])] = int(item["count"])

        source_cursor = await self.collection.aggregate(
            [
                {"$match": self._window_query(date_from, date_to)},
                {
                    "$group": {
                        "_id": {
                            "$ifNull": [
                                "$event_source",
                                AnalyticsEventSource.PUBLIC.value,
                            ]
                        },
                        "count": {"$sum": 1},
                    }
                },
            ]
        )
        source_counts: dict[str, int] = {}
        async for item in source_cursor:
            if item.get("_id") is not None:
                source_counts[str(item["_id"])] = int(item["count"])

        return {
            "registrations": await self._count_in_window(
                "users", date_from, date_to
            ),
            "questionnaires_completed": server_event_counts.get(
                AnalyticsEventType.QUESTIONNAIRE_COMPLETED.value,
                0,
            ),
            "recommendations_generated": await self._count_in_window(
                "recommendation_sessions", date_from, date_to
            ),
            "feedback_submitted": await self._count_in_window(
                "feedback_events", date_from, date_to
            ),
            "replacement_sessions": await self._count_in_window(
                "replacement_sessions", date_from, date_to
            ),
            "replacement_selections": await self._count_in_window(
                "replacement_sessions",
                date_from,
                date_to,
                {
                    "selected_product_external_id": {
                        "$exists": True,
                        "$nin": [None, ""],
                    }
                },
            ),
            "recommendation_shares": await self._count_in_window(
                "analytics_events",
                date_from,
                date_to,
                {"event_type": AnalyticsEventType.RECOMMENDATION_SHARED.value},
            ),
            "llm_success": server_event_counts.get(
                AnalyticsEventType.LLM_EXPLANATION_SUCCESS.value,
                0,
            ),
            "llm_fallback": server_event_counts.get(
                AnalyticsEventType.LLM_EXPLANATION_FALLBACK.value,
                0,
            ),
            "public_events": source_counts.get(
                AnalyticsEventSource.PUBLIC.value,
                0,
            ),
            "server_events": source_counts.get(
                AnalyticsEventSource.SERVER.value,
                0,
            ),
        }

    async def dashboard_activity(
        self,
        date_from: datetime,
        date_to: datetime,
    ) -> dict[str, dict[str, int]]:
        events_by_source_cursor = await self.collection.aggregate(
            [
                {"$match": self._window_query(date_from, date_to)},
                {
                    "$group": {
                        "_id": {
                            "date": {
                                "$dateToString": {
                                    "format": "%Y-%m-%d",
                                    "date": "$created_at",
                                    "timezone": "UTC",
                                }
                            },
                            "source": {
                                "$ifNull": [
                                    "$event_source",
                                    AnalyticsEventSource.PUBLIC.value,
                                ]
                            },
                        },
                        "count": {"$sum": 1},
                    }
                },
            ]
        )
        public_events: dict[str, int] = {}
        server_events: dict[str, int] = {}
        async for item in events_by_source_cursor:
            key = item.get("_id") or {}
            date_key = str(key.get("date"))
            source = str(key.get("source"))
            if source == AnalyticsEventSource.SERVER.value:
                server_events[date_key] = int(item["count"])
            else:
                public_events[date_key] = int(item["count"])

        return {
            "registrations": await self._group_collection_by_day(
                "users", date_from, date_to
            ),
            "questionnaires_completed": await self._group_server_event_by_day(
                AnalyticsEventType.QUESTIONNAIRE_COMPLETED,
                date_from,
                date_to,
            ),
            "recommendations_generated": await self._group_collection_by_day(
                "recommendation_sessions", date_from, date_to
            ),
            "feedback_submitted": await self._group_collection_by_day(
                "feedback_events", date_from, date_to
            ),
            "replacement_sessions": await self._group_collection_by_day(
                "replacement_sessions", date_from, date_to
            ),
            "replacement_selections": await self._group_collection_by_day(
                "replacement_sessions",
                date_from,
                date_to,
                {
                    "selected_product_external_id": {
                        "$exists": True,
                        "$nin": [None, ""],
                    }
                },
            ),
            "recommendation_shares": await self._group_collection_by_day(
                "analytics_events",
                date_from,
                date_to,
                {"event_type": AnalyticsEventType.RECOMMENDATION_SHARED.value},
            ),
            "llm_success": await self._group_server_event_by_day(
                AnalyticsEventType.LLM_EXPLANATION_SUCCESS,
                date_from,
                date_to,
            ),
            "llm_fallback": await self._group_server_event_by_day(
                AnalyticsEventType.LLM_EXPLANATION_FALLBACK,
                date_from,
                date_to,
            ),
            "public_events": public_events,
            "server_events": server_events,
        }

    async def dashboard_top_recommended_products(
        self,
        date_from: datetime,
        date_to: datetime,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        morning_ids = {
            "$map": {
                "input": {"$ifNull": ["$result.routine.morning", []]},
                "as": "item",
                "in": "$$item.product.external_id",
            }
        }
        evening_ids = {
            "$map": {
                "input": {"$ifNull": ["$result.routine.evening", []]},
                "as": "item",
                "in": "$$item.product.external_id",
            }
        }
        cursor = await self.database["recommendation_sessions"].aggregate(
            [
                {"$match": self._window_query(date_from, date_to)},
                {
                    "$project": {
                        "product_external_ids": {
                            "$filter": {
                                "input": {"$setUnion": [morning_ids, evening_ids]},
                                "as": "product_id",
                                "cond": {
                                    "$and": [
                                        {"$ne": ["$$product_id", None]},
                                        {"$ne": ["$$product_id", ""]},
                                    ]
                                },
                            }
                        }
                    }
                },
                {"$unwind": "$product_external_ids"},
                {
                    "$group": {
                        "_id": "$product_external_ids",
                        "count": {"$sum": 1},
                    }
                },
                {"$sort": {"count": -1, "_id": 1}},
                {"$limit": limit},
            ]
        )

        result: list[dict[str, Any]] = []
        async for item in cursor:
            result.append(
                {
                    "product_external_id": str(item["_id"]),
                    "count": int(item["count"]),
                }
            )
        return result

    async def dashboard_product_counts(
        self,
        collection_name: str,
        field: str,
        date_from: datetime,
        date_to: datetime,
        *,
        limit: int = 10,
        require_non_empty: bool = True,
    ) -> list[dict[str, Any]]:
        query = self._window_query(date_from, date_to)
        if require_non_empty:
            query[field] = {"$exists": True, "$nin": [None, ""]}

        cursor = await self.database[collection_name].aggregate(
            [
                {"$match": query},
                {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
                {"$sort": {"count": -1, "_id": 1}},
                {"$limit": limit},
            ]
        )

        result: list[dict[str, Any]] = []
        async for item in cursor:
            if item.get("_id") not in {None, ""}:
                result.append(
                    {
                        "product_external_id": str(item["_id"]),
                        "count": int(item["count"]),
                    }
                )
        return result

    async def dashboard_feedback_reasons(
        self,
        date_from: datetime,
        date_to: datetime,
    ) -> dict[str, int]:
        cursor = await self.database["feedback_events"].aggregate(
            [
                {"$match": self._window_query(date_from, date_to)},
                {"$match": {"reason": {"$nin": [None, ""]}}},
                {"$group": {"_id": "$reason", "count": {"$sum": 1}}},
                {"$sort": {"count": -1, "_id": 1}},
            ]
        )
        result: dict[str, int] = {}
        async for item in cursor:
            result[str(item["_id"])] = int(item["count"])
        return result

    async def dashboard_feedback_reasons_by_product(
        self,
        date_from: datetime,
        date_to: datetime,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        cursor = await self.database["feedback_events"].aggregate(
            [
                {"$match": self._window_query(date_from, date_to)},
                {
                    "$match": {
                        "product_external_id": {"$nin": [None, ""]},
                        "reason": {"$nin": [None, ""]},
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "product_external_id": "$product_external_id",
                            "reason": "$reason",
                        },
                        "count": {"$sum": 1},
                    }
                },
                {
                    "$group": {
                        "_id": "$_id.product_external_id",
                        "count": {"$sum": "$count"},
                        "reasons": {
                            "$push": {
                                "reason": "$_id.reason",
                                "count": "$count",
                            }
                        },
                    }
                },
                {"$sort": {"count": -1, "_id": 1}},
                {"$limit": limit},
            ]
        )

        result: list[dict[str, Any]] = []
        async for item in cursor:
            result.append(
                {
                    "product_external_id": str(item["_id"]),
                    "count": int(item["count"]),
                    "reasons": {
                        str(reason["reason"]): int(reason["count"])
                        for reason in item.get("reasons", [])
                    },
                }
            )
        return result

    async def dashboard_replacement_reasons(
        self,
        date_from: datetime,
        date_to: datetime,
    ) -> dict[str, int]:
        cursor = await self.database["replacement_sessions"].aggregate(
            [
                {"$match": self._window_query(date_from, date_to)},
                {"$match": {"reason": {"$nin": [None, ""]}}},
                {"$group": {"_id": "$reason", "count": {"$sum": 1}}},
                {"$sort": {"count": -1, "_id": 1}},
            ]
        )
        result: dict[str, int] = {}
        async for item in cursor:
            result[str(item["_id"])] = int(item["count"])
        return result

    async def dashboard_audience(
        self,
        date_from: datetime,
        date_to: datetime,
    ) -> dict[str, dict[str, int]]:
        restriction_cursor = await self.database["recommendation_sessions"].aggregate(
            [
                {"$match": self._window_query(date_from, date_to)},
                {
                    "$project": {
                        "restrictions": {
                            "$setUnion": [
                                {
                                    "$ifNull": [
                                        "$request.excluded_ingredients",
                                        [],
                                    ]
                                },
                                {
                                    "$cond": [
                                        {
                                            "$gt": [
                                                {
                                                    "$size": {
                                                        "$ifNull": [
                                                            "$request.custom_restrictions",
                                                            [],
                                                        ]
                                                    }
                                                },
                                                0,
                                            ]
                                        },
                                        ["custom"],
                                        [],
                                    ]
                                },
                            ]
                        }
                    }
                },
                {"$unwind": "$restrictions"},
                {"$match": {"restrictions": {"$nin": [None, ""]}}},
                {"$group": {"_id": "$restrictions", "count": {"$sum": 1}}},
                {"$sort": {"count": -1, "_id": 1}},
                {"$limit": 20},
            ]
        )
        restrictions: dict[str, int] = {}
        async for item in restriction_cursor:
            restrictions[str(item["_id"])] = int(item["count"])

        return {
            "skin_types": await self._distribution(
                "request.skin_type",
                date_from,
                date_to,
                array=False,
            ),
            "concerns": await self._distribution(
                "request.concerns",
                date_from,
                date_to,
                array=True,
            ),
            "restrictions": restrictions,
            "budgets": await self._distribution(
                "request.budget",
                date_from,
                date_to,
                array=False,
            ),
            "experience": await self._distribution(
                "request.experience",
                date_from,
                date_to,
                array=False,
            ),
        }

    async def product_labels(
        self,
        product_external_ids: set[str],
    ) -> dict[str, dict[str, str | None]]:
        if not product_external_ids:
            return {}

        cursor = self.database["products"].find(
            {"external_id": {"$in": sorted(product_external_ids)}},
            {"_id": 0, "external_id": 1, "name": 1, "brand": 1},
        )

        result: dict[str, dict[str, str | None]] = {}
        async for document in cursor:
            external_id = document.get("external_id")
            if external_id is None:
                continue
            result[str(external_id)] = {
                "name": document.get("name"),
                "brand": document.get("brand"),
            }
        return result
