from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "sunwise_koyash_review"
if not ROOT.exists():
    ROOT = Path(r"C:\Projects\sunwise-koyash")


def write(relative: str, content: str) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")
    ast.parse(path.read_text(encoding="utf-8")) if path.suffix == ".py" else None


# 1. Enums: append only when missing.
enums_path = ROOT / "backend/app/core/enums.py"
enums_text = enums_path.read_text(encoding="utf-8-sig")
if "class UserRole(StrEnum):" not in enums_text:
    enums_text = enums_text.rstrip() + '''\n\n\nclass UserRole(StrEnum):\n    USER = "user"\n    ADMIN = "admin"\n\n\nclass PublicAnalyticsEventType(StrEnum):\n    QUESTIONNAIRE_OPENED = "questionnaire_opened"\n    QUESTIONNAIRE_STARTED = "questionnaire_started"\n    QUESTION_ANSWERED = "question_answered"\n    QUESTIONNAIRE_COMPLETED = "questionnaire_completed"\n    RESULT_VIEWED = "result_viewed"\n    PRODUCT_VIEWED = "product_viewed"\n    PRODUCT_DETAILS_OPENED = "product_details_opened"\n'''
    enums_path.write_text(enums_text, encoding="utf-8")
ast.parse(enums_path.read_text(encoding="utf-8"))

# 2. Auth/user schemas: forbid privilege-field injection and expose read-only role.
write(
    "backend/app/schemas/auth.py",
    '''
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.user import UserProfileResponse, UserResponse


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=120)
    anonymous_id: str | None = Field(default=None, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    profile: UserProfileResponse


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    dev_reset_url: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20)
    new_password: str = Field(min_length=8, max_length=128)


class ResetPasswordResponse(BaseModel):
    message: str
''',
)

write(
    "backend/app/schemas/user.py",
    '''
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.enums import UserRole


class UserResponse(BaseModel):
    user_id: str
    email: EmailStr
    full_name: str | None = None
    anonymous_id: str | None = None
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    last_seen_at: datetime


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, max_length=120)
    anonymous_id: str | None = Field(default=None, max_length=120)


class QuestionnaireHistoryCreate(BaseModel):
    recommendation_id: str | None = Field(default=None, max_length=120)
    age: int | None = Field(default=None, ge=12, le=100)
    skin_type: str | None = None
    concerns: list[str] = Field(default_factory=list)
    budget: str | None = None
    excluded_ingredients: list[str] = Field(default_factory=list)
    custom_restrictions: list[str] = Field(default_factory=list)
    experience: str | None = None
    values: list[str] = Field(default_factory=list)
    total_price_rub: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class UserProfileResponse(BaseModel):
    profile_id: str
    user_id: str
    anonymous_id: str | None = None
    age: int | None = Field(default=None, ge=12, le=100)
    skin_type: str | None = None
    concerns: list[str] = Field(default_factory=list)
    budget: str | None = None
    excluded_ingredients: list[str] = Field(default_factory=list)
    custom_restrictions: list[str] = Field(default_factory=list)
    experience: str | None = None
    values: list[str] = Field(default_factory=list)
    questionnaire_history: list[dict[str, Any]] = Field(default_factory=list)
    feedback_history: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class UserProfileUpdate(BaseModel):
    age: int | None = Field(default=None, ge=12, le=100)
    skin_type: str | None = None
    concerns: list[str] | None = None
    budget: str | None = None
    excluded_ingredients: list[str] | None = None
    custom_restrictions: list[str] | None = None
    experience: str | None = None
    values: list[str] | None = None
''',
)

# 3. User repository: role defaults, legacy fallback, explicit admin-only CLI method.
write(
    "backend/app/repositories/user_repository.py",
    '''
from typing import Any

from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase

from app.core.enums import UserRole
from app.core.time import utc_now


def _clean_user(document: dict[str, Any], include_password_hash: bool = False) -> dict[str, Any]:
    document["user_id"] = str(document.pop("_id"))
    document.setdefault("role", UserRole.USER.value)

    if not include_password_hash:
        document.pop("password_hash", None)

    return document


class UserRepository:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.collection = database["users"]

    async def create_user(
        self,
        email: str,
        password_hash: str,
        full_name: str | None = None,
        anonymous_id: str | None = None,
    ) -> dict[str, Any]:
        now = utc_now()

        document = {
            "email": email.lower(),
            "password_hash": password_hash,
            "full_name": full_name,
            "anonymous_id": anonymous_id,
            "role": UserRole.USER.value,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
            "last_seen_at": now,
        }

        result = await self.collection.insert_one(document)
        document["_id"] = result.inserted_id

        return _clean_user(document)

    async def find_by_email(
        self,
        email: str,
        include_password_hash: bool = False,
    ) -> dict[str, Any] | None:
        document = await self.collection.find_one({"email": email.lower()})

        if document is None:
            return None

        return _clean_user(document, include_password_hash=include_password_hash)

    async def find_by_id(
        self,
        user_id: str,
        include_password_hash: bool = False,
    ) -> dict[str, Any] | None:
        if not ObjectId.is_valid(user_id):
            return None

        document = await self.collection.find_one({"_id": ObjectId(user_id)})

        if document is None:
            return None

        return _clean_user(document, include_password_hash=include_password_hash)

    async def update_last_seen(self, user_id: str) -> None:
        if not ObjectId.is_valid(user_id):
            return

        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"last_seen_at": utc_now()}},
        )

    async def update_user(
        self,
        user_id: str,
        full_name: str | None = None,
        anonymous_id: str | None = None,
    ) -> dict[str, Any] | None:
        if not ObjectId.is_valid(user_id):
            return None

        update: dict[str, Any] = {"updated_at": utc_now()}

        if full_name is not None:
            update["full_name"] = full_name

        if anonymous_id is not None:
            update["anonymous_id"] = anonymous_id

        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update},
        )

        return await self.find_by_id(user_id)

    async def update_password(
        self,
        user_id: str,
        password_hash: str,
    ) -> bool:
        if not ObjectId.is_valid(user_id):
            return False

        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "password_hash": password_hash,
                    "updated_at": utc_now(),
                }
            },
        )

        return result.modified_count == 1

    async def set_role_by_email(
        self,
        email: str,
        role: UserRole,
    ) -> dict[str, Any] | None:
        result = await self.collection.update_one(
            {"email": email.lower()},
            {
                "$set": {
                    "role": role.value,
                    "updated_at": utc_now(),
                }
            },
        )

        if result.matched_count != 1:
            return None

        return await self.find_by_email(email)
''',
)

# 4. Authentication dependencies: required, optional, and admin-only.
write(
    "backend/app/api/v1/dependencies.py",
    '''
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import get_settings
from app.core.enums import UserRole
from app.core.security import decode_access_token
from app.db.mongodb import get_database
from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.email_service import EmailService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
optional_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token",
    auto_error=False,
)


def get_auth_service(database=Depends(get_database)) -> AuthService:
    settings = get_settings()

    return AuthService(
        user_repository=UserRepository(database),
        profile_repository=ProfileRepository(database),
        password_reset_repository=PasswordResetRepository(database),
        email_service=EmailService(settings),
    )


async def _resolve_user_from_token(
    token: str,
    auth_service: AuthService,
) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")

    if not user_id:
        raise credentials_exception

    user = await auth_service.user_repository.find_by_id(user_id)

    if user is None:
        raise credentials_exception

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    return user


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> dict:
    return await _resolve_user_from_token(token, auth_service)


async def get_optional_current_user(
    token: Annotated[str | None, Depends(optional_oauth2_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> dict | None:
    if token is None:
        return None

    return await _resolve_user_from_token(token, auth_service)


async def require_admin(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    role = str(current_user.get("role") or UserRole.USER.value)

    if role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user
''',
)

# 5. Public analytics schema: no user_id spoofing, no server-event spoofing, bounded metadata.
write(
    "backend/app/schemas/analytics.py",
    '''
import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import PublicAnalyticsEventType


_FORBIDDEN_METADATA_KEYS = {
    "authorization",
    "email",
    "full_name",
    "password",
    "phone",
    "secret",
    "token",
    "user_id",
    "anonymous_id",
}


def _metadata_keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        result: list[str] = []
        for key, item in value.items():
            result.append(str(key).casefold())
            result.extend(_metadata_keys(item))
        return result

    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(_metadata_keys(item))
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

        forbidden = sorted(set(_metadata_keys(value)).intersection(_FORBIDDEN_METADATA_KEYS))
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
''',
)

write(
    "backend/app/services/analytics_service.py",
    '''
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import (
    AnalyticsEventCreate,
    AnalyticsEventResponse,
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
''',
)

write(
    "backend/app/api/v1/endpoints/analytics.py",
    '''
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
''',
)

# 6. Admin route: role-protected and absent from OpenAPI.
write(
    "backend/app/api/v1/endpoints/admin_analytics.py",
    '''
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import require_admin
from app.db.mongodb import get_database
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import AnalyticsSummaryResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/admin/analytics", tags=["admin analytics"])


def get_analytics_service(database=Depends(get_database)) -> AnalyticsService:
    return AnalyticsService(
        analytics_repository=AnalyticsRepository(database),
    )


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
''',
)

# 7. Recent admin events: data minimization; raw identifiers stay in DB only.
write(
    "backend/app/repositories/analytics_repository.py",
    '''
from typing import Any

from bson import ObjectId
from pymongo import DESCENDING
from pymongo.asynchronous.database import AsyncDatabase

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
    ) -> dict[str, Any]:
        document = {
            "event_type": event_type,
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
                    "event_id": str(document["_id"]),
                    "event_type": document.get("event_type"),
                    "recommendation_id": document.get("recommendation_id"),
                    "product_external_id": document.get("product_external_id"),
                    "metadata": document.get("metadata") or {},
                    "created_at": document.get("created_at"),
                }
            )

        return result

    async def clear_event(self, event_id: str) -> bool:
        if not ObjectId.is_valid(event_id):
            return False

        result = await self.collection.delete_one({"_id": ObjectId(event_id)})
        return result.deleted_count == 1
''',
)

# 8. Add users.role index without changing other indexes.
indexes_path = ROOT / "backend/app/db/indexes.py"
indexes_text = indexes_path.read_text(encoding="utf-8-sig")
role_index_line = '    await _create_index_safely(database["users"], "role")\n'
email_index_line = '    await _create_index_safely(database["users"], "email", unique=True)\n'
if role_index_line not in indexes_text:
    if email_index_line not in indexes_text:
        raise RuntimeError("Could not find users email index insertion point")
    indexes_text = indexes_text.replace(email_index_line, email_index_line + role_index_line, 1)
indexes_path.write_text(indexes_text, encoding="utf-8")
ast.parse(indexes_path.read_text(encoding="utf-8"))

# 9. Safe role-management CLI: existing user only, dry-run by default.
write(
    "backend/scripts/set_user_role.py",
    '''
import argparse
import asyncio
import json
import sys
from typing import Any

from pydantic import EmailStr, TypeAdapter, ValidationError
from pymongo import AsyncMongoClient

from app.core.config import get_settings
from app.core.enums import UserRole
from app.core.time import utc_now


async def set_role(email: str, role: UserRole, apply_change: bool) -> dict[str, Any]:
    settings = get_settings()
    client: AsyncMongoClient[Any] = AsyncMongoClient(
        settings.mongo_uri,
        uuidRepresentation="standard",
    )

    try:
        await client.admin.command("ping")
        users = client[settings.mongo_db_name]["users"]
        user = await users.find_one({"email": email})

        if user is None:
            return {
                "ok": False,
                "database": settings.mongo_db_name,
                "email": email,
                "error": "user_not_found",
            }

        previous_role = str(user.get("role") or UserRole.USER.value)

        if apply_change:
            await users.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "role": role.value,
                        "updated_at": utc_now(),
                    }
                },
            )

        return {
            "ok": True,
            "applied": apply_change,
            "database": settings.mongo_db_name,
            "user_id": str(user["_id"]),
            "email": email,
            "previous_role": previous_role,
            "requested_role": role.value,
        }
    finally:
        await client.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Safely set role for an existing KOYASH user.",
    )
    parser.add_argument("--email", required=True)
    parser.add_argument(
        "--role",
        required=True,
        choices=[role.value for role in UserRole],
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the change. Without this flag the command is a dry run.",
    )
    args = parser.parse_args()

    try:
        email = str(TypeAdapter(EmailStr).validate_python(args.email)).lower()
    except ValidationError as exc:
        print(json.dumps({"ok": False, "error": "invalid_email"}, indent=2))
        raise SystemExit(2) from exc

    report = asyncio.run(
        set_role(
            email=email,
            role=UserRole(args.role),
            apply_change=args.apply,
        )
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if not report["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
''',
)

# 10. Replace analytics tests with security-focused contract tests.
write(
    "backend/tests/test_analytics.py",
    '''
from uuid import uuid4

from fastapi.testclient import TestClient
from pymongo import MongoClient

from app.core.config import get_settings
from app.main import app


def _register(client: TestClient) -> tuple[str, dict]:
    email = f"analytics-{uuid4().hex}@example.com"
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "Analytics User",
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"], response.json()["user"]


def _set_role(email: str, role: str) -> None:
    settings = get_settings()
    client = MongoClient(
        settings.mongo_uri,
        uuidRepresentation="standard",
        serverSelectionTimeoutMS=5000,
    )
    try:
        result = client[settings.mongo_db_name]["users"].update_one(
            {"email": email.lower()},
            {"$set": {"role": role}},
        )
        assert result.matched_count == 1
    finally:
        client.close()


def test_public_analytics_event_can_be_recorded_anonymously() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/analytics/events",
            json={
                "event_type": "product_viewed",
                "anonymous_id": "analytics-test",
                "product_external_id": "cleanser_001",
                "metadata": {"source": "test"},
            },
        )

    assert response.status_code == 201
    assert response.json()["status"] == "recorded"


def test_public_analytics_rejects_server_owned_event_type() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/analytics/events",
            json={
                "event_type": "feedback_submitted",
                "metadata": {"source": "spoofed"},
            },
        )

    assert response.status_code == 422


def test_public_analytics_rejects_user_id_spoofing() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/analytics/events",
            json={
                "event_type": "result_viewed",
                "user_id": "forged-user-id",
                "metadata": {},
            },
        )

    assert response.status_code == 422


def test_admin_summary_without_token_returns_401() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/admin/analytics/summary")

    assert response.status_code == 401


def test_admin_summary_for_regular_user_returns_403() -> None:
    with TestClient(app) as client:
        token, _ = _register(client)
        response = client.get(
            "/api/v1/admin/analytics/summary",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_admin_summary_for_admin_returns_200() -> None:
    with TestClient(app) as client:
        token, user = _register(client)
        _set_role(user["email"], "admin")

        response = client.get(
            "/api/v1/admin/analytics/summary",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert "total_events" in payload
    assert "events_by_type" in payload
    assert "recent_events" in payload


def test_admin_summary_is_hidden_from_openapi() -> None:
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    assert "/api/v1/admin/analytics/summary" not in schema["paths"]
''',
)

# 11. Add privilege-escalation tests to auth suite without rewriting existing tests.
auth_tests_path = ROOT / "backend/tests/test_auth_users.py"
auth_tests_text = auth_tests_path.read_text(encoding="utf-8-sig")
security_tests = '''\n\ndef test_registered_user_has_user_role() -> None:\n    with TestClient(app) as client:\n        _, payload = _register_user(client)\n\n    assert payload["user"]["role"] == "user"\n\n\ndef test_registration_rejects_role_injection() -> None:\n    with TestClient(app) as client:\n        response = client.post(\n            "/api/v1/auth/register",\n            json={\n                "email": _unique_email(),\n                "password": "StrongPassword123!",\n                "full_name": "Injected Admin",\n                "role": "admin",\n            },\n        )\n\n    assert response.status_code == 422\n\n\ndef test_profile_update_rejects_role_injection() -> None:\n    with TestClient(app) as client:\n        token, _ = _register_user(client)\n        response = client.patch(\n            "/api/v1/users/me",\n            headers={"Authorization": f"Bearer {token}"},\n            json={\n                "full_name": "Still User",\n                "role": "admin",\n            },\n        )\n\n    assert response.status_code == 422\n'''
if "test_registration_rejects_role_injection" not in auth_tests_text:
    auth_tests_path.write_text(auth_tests_text.rstrip() + security_tests + "\n", encoding="utf-8")
ast.parse(auth_tests_path.read_text(encoding="utf-8"))

# 12. Add security documentation.
write(
    "docs/admin-security.md",
    '''
# KOYASH admin security boundary

The admin analytics API is intentionally not shown in OpenAPI/Swagger and is not linked from the normal user interface.

Access rules:

- no bearer token: `401`;
- active user with role `user`: `403`;
- active user with role `admin`: allowed;
- inactive users remain blocked;
- registration and profile update reject the `role` field;
- JWT stores only the user id, while the current role is loaded from MongoDB on every request, so demotion takes effect immediately.

The public analytics endpoint accepts only client-safe UI event types. Server-owned events such as feedback, registration and replacement selection must be written by backend services, not supplied by a browser. The browser cannot submit `user_id`; authenticated identity is derived from the bearer token.

## Promote an existing user

Dry run:

```bash
docker compose exec -T backend python scripts/set_user_role.py --email admin@example.com --role admin
```

Apply:

```bash
docker compose exec -T backend python scripts/set_user_role.py --email admin@example.com --role admin --apply
```

Demotion uses the same command with `--role user --apply`.
''',
)

# Final syntax verification for all backend Python files touched by this step.
for path in [
    enums_path,
    ROOT / "backend/app/schemas/auth.py",
    ROOT / "backend/app/schemas/user.py",
    ROOT / "backend/app/repositories/user_repository.py",
    ROOT / "backend/app/api/v1/dependencies.py",
    ROOT / "backend/app/schemas/analytics.py",
    ROOT / "backend/app/services/analytics_service.py",
    ROOT / "backend/app/api/v1/endpoints/analytics.py",
    ROOT / "backend/app/api/v1/endpoints/admin_analytics.py",
    ROOT / "backend/app/repositories/analytics_repository.py",
    indexes_path,
    ROOT / "backend/scripts/set_user_role.py",
    ROOT / "backend/tests/test_analytics.py",
    auth_tests_path,
]:
    ast.parse(path.read_text(encoding="utf-8-sig"))

print("STEP 4.9A APPLIED")
print("- admin analytics requires database role=admin")
print("- admin route is hidden from OpenAPI")
print("- registration/profile role injection is rejected")
print("- public analytics cannot spoof user_id or server-owned events")
