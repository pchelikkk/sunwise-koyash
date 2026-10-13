from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path.cwd()

REQUIRED = [
    "backend/app/core/enums.py",
    "backend/app/api/v1/dependencies.py",
    "backend/app/repositories/analytics_repository.py",
    "backend/app/services/auth_service.py",
    "backend/app/services/recommendation_service.py",
]

for relative in REQUIRED:
    if not (ROOT / relative).exists():
        raise RuntimeError(
            f"Run this script from the repository root. Missing: {relative}"
        )

if "class UserRole(StrEnum):" not in (ROOT / "backend/app/core/enums.py").read_text(
    encoding="utf-8-sig"
):
    raise RuntimeError("Step 4.9A is not present: UserRole was not found")

if "async def require_admin" not in (
    ROOT / "backend/app/api/v1/dependencies.py"
).read_text(encoding="utf-8-sig"):
    raise RuntimeError("Step 4.9A is not present: require_admin was not found")


def write(relative: str, content: str) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")
    if path.suffix == ".py":
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


write(
    "backend/app/core/enums.py",
    '''
from enum import StrEnum


class SkinType(StrEnum):
    OILY = "oily"
    DRY = "dry"
    COMBINATION = "combination"
    SENSITIVE = "sensitive"
    NORMAL = "normal"


class Concern(StrEnum):
    ACNE = "acne"
    SEBUM = "sebum"
    DRYNESS = "dryness"
    POST_ACNE = "post_acne"
    UNEVEN_TONE = "uneven_tone"
    SENSITIVITY = "sensitivity"
    AGE_CHANGES = "age_changes"
    UNKNOWN = "unknown"


class BudgetSegment(StrEnum):
    MINIMUM = "minimum"
    BALANCED = "balanced"
    PREMIUM = "premium"


class ExperienceLevel(StrEnum):
    BEGINNER = "beginner"
    BASIC = "basic"
    ADVANCED = "advanced"
    MINIMAL = "minimal"


class RoutineStep(StrEnum):
    CLEANSER = "cleanser"
    SERUM = "serum"
    TREATMENT = "treatment"
    MOISTURIZER = "moisturizer"
    SPF = "spf"


class RestrictionStatus(StrEnum):
    APPROVED = "approved"
    PENDING = "pending"
    HIDDEN = "hidden"
    BLOCKED = "blocked"


class AnalyticsEventType(StrEnum):
    QUESTIONNAIRE_STARTED = "questionnaire_started"
    QUESTION_ANSWERED = "question_answered"
    QUESTIONNAIRE_COMPLETED = "questionnaire_completed"
    RECOMMENDATION_REQUESTED = "recommendation_requested"
    RECOMMENDATION_GENERATED = "recommendation_generated"
    RESULT_VIEWED = "result_viewed"
    PRODUCT_DETAILS_OPENED = "product_details_opened"
    FEEDBACK_SUBMITTED = "feedback_submitted"
    REPLACEMENT_GENERATED = "replacement_generated"
    REPLACEMENT_SELECTED = "replacement_selected"
    REGISTRATION_COMPLETED = "registration_completed"
    PROFILE_SAVED = "profile_saved"
    LLM_EXPLANATION_SUCCESS = "llm_explanation_success"
    LLM_EXPLANATION_FALLBACK = "llm_explanation_fallback"


class AnalyticsEventSource(StrEnum):
    PUBLIC = "public"
    SERVER = "server"


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class PublicAnalyticsEventType(StrEnum):
    QUESTIONNAIRE_OPENED = "questionnaire_opened"
    QUESTIONNAIRE_STARTED = "questionnaire_started"
    QUESTION_ANSWERED = "question_answered"
    RESULT_VIEWED = "result_viewed"
    PRODUCT_VIEWED = "product_viewed"
    PRODUCT_DETAILS_OPENED = "product_details_opened"
''',
)

write(
    "backend/app/repositories/analytics_repository.py",
    '''
from typing import Any

from bson import ObjectId
from pymongo import DESCENDING
from pymongo.asynchronous.database import AsyncDatabase

from app.core.enums import AnalyticsEventSource
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
                    "event_id": str(document["_id"]),
                    "event_type": document.get("event_type"),
                    "event_source": document.get(
                        "event_source",
                        AnalyticsEventSource.PUBLIC.value,
                    ),
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

write(
    "backend/app/services/analytics_service.py",
    '''
from app.core.enums import AnalyticsEventSource
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
''',
)

write(
    "backend/app/services/event_tracking_service.py",
    '''
import json
import logging
from enum import Enum
from typing import Any

from app.core.enums import AnalyticsEventSource, AnalyticsEventType
from app.repositories.analytics_repository import AnalyticsRepository

logger = logging.getLogger(__name__)

_FORBIDDEN_METADATA_KEYS = {
    "anonymous_id",
    "authorization",
    "comment",
    "email",
    "full_name",
    "password",
    "phone",
    "secret",
    "token",
    "user_id",
}


def _sanitize_value(value: Any, depth: int = 0) -> Any:
    if depth > 4:
        return str(value)[:240]

    if value is None or isinstance(value, bool | int | float):
        return value

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, str):
        return value[:240]

    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in list(value.items())[:30]:
            normalized_key = str(key).casefold()
            if normalized_key in _FORBIDDEN_METADATA_KEYS:
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
''',
)

write(
    "backend/app/services/auth_service.py",
    '''
from datetime import timedelta
from urllib.parse import urlencode

from app.core.config import get_settings
from app.core.enums import AnalyticsEventType
from app.core.security import (
    create_access_token,
    create_password_hash,
    create_secure_token,
    hash_password_reset_token,
    verify_password,
)
from app.core.time import utc_now
from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    AuthResponse,
    ForgotPasswordResponse,
    RegisterRequest,
    ResetPasswordResponse,
)
from app.schemas.user import UserProfileResponse, UserResponse
from app.services.email_service import EmailService
from app.services.event_tracking_service import EventTrackingService


class DuplicateEmailError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InvalidResetTokenError(Exception):
    pass


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        profile_repository: ProfileRepository,
        password_reset_repository: PasswordResetRepository,
        email_service: EmailService,
        event_tracking_service: EventTrackingService | None = None,
    ) -> None:
        self.user_repository = user_repository
        self.profile_repository = profile_repository
        self.password_reset_repository = password_reset_repository
        self.email_service = email_service
        self.event_tracking_service = event_tracking_service

    async def register(self, payload: RegisterRequest) -> AuthResponse:
        email = payload.email.lower()
        existing = await self.user_repository.find_by_email(email)

        if existing is not None:
            raise DuplicateEmailError

        user = await self.user_repository.create_user(
            email=email,
            password_hash=create_password_hash(payload.password),
            full_name=payload.full_name,
            anonymous_id=payload.anonymous_id,
        )

        profile = await self.profile_repository.ensure_profile(
            user_id=user["user_id"],
            anonymous_id=user.get("anonymous_id"),
        )

        if self.event_tracking_service is not None:
            await self.event_tracking_service.record(
                AnalyticsEventType.REGISTRATION_COMPLETED,
                user_id=user["user_id"],
                anonymous_id=user.get("anonymous_id"),
                metadata={
                    "name_provided": bool(payload.full_name),
                    "pre_registration_session_linked": bool(payload.anonymous_id),
                },
            )

        return self._build_auth_response(user=user, profile=profile)

    async def login(self, email: str, password: str) -> AuthResponse:
        user_with_password = await self.user_repository.find_by_email(
            email.lower(),
            include_password_hash=True,
        )

        if user_with_password is None:
            raise InvalidCredentialsError

        if not verify_password(password, user_with_password["password_hash"]):
            raise InvalidCredentialsError

        await self.user_repository.update_last_seen(user_with_password["user_id"])

        user = await self.user_repository.find_by_id(user_with_password["user_id"])

        if user is None:
            raise InvalidCredentialsError

        profile = await self.profile_repository.ensure_profile(
            user_id=user["user_id"],
            anonymous_id=user.get("anonymous_id"),
        )

        return self._build_auth_response(user=user, profile=profile)

    async def forgot_password(self, email: str) -> ForgotPasswordResponse:
        settings = get_settings()
        message = "Если аккаунт существует, инструкция по сбросу пароля будет отправлена."

        user = await self.user_repository.find_by_email(email.lower())

        if user is None:
            return ForgotPasswordResponse(message=message)

        raw_token = create_secure_token()
        token_hash = hash_password_reset_token(raw_token)
        expires_at = utc_now() + timedelta(
            minutes=settings.password_reset_token_expire_minutes,
        )

        await self.password_reset_repository.invalidate_user_tokens(user["user_id"])
        await self.password_reset_repository.create_token(
            user_id=user["user_id"],
            email=user["email"],
            token_hash=token_hash,
            expires_at=expires_at,
        )

        reset_url = self._build_reset_url(raw_token)
        await self.email_service.send_password_reset_email(
            to_email=user["email"],
            reset_url=reset_url,
        )

        dev_reset_url = None if settings.is_production else reset_url

        return ForgotPasswordResponse(
            message=message,
            dev_reset_url=dev_reset_url,
        )

    async def reset_password(
        self,
        token: str,
        new_password: str,
    ) -> ResetPasswordResponse:
        token_hash = hash_password_reset_token(token)
        reset_token = await self.password_reset_repository.find_valid_by_hash(token_hash)

        if reset_token is None:
            raise InvalidResetTokenError

        new_password_hash = create_password_hash(new_password)

        updated = await self.user_repository.update_password(
            user_id=reset_token["user_id"],
            password_hash=new_password_hash,
        )

        if not updated:
            raise InvalidResetTokenError

        await self.password_reset_repository.mark_used(reset_token["reset_id"])
        await self.password_reset_repository.invalidate_user_tokens(reset_token["user_id"])

        return ResetPasswordResponse(message="Пароль успешно обновлён.")

    def _build_auth_response(
        self,
        user: dict,
        profile: dict,
    ) -> AuthResponse:
        return AuthResponse(
            access_token=create_access_token(user["user_id"]),
            token_type="bearer",
            user=UserResponse(**user),
            profile=UserProfileResponse(**profile),
        )

    def _build_reset_url(self, token: str) -> str:
        settings = get_settings()
        base_url = settings.frontend_base_url.rstrip("/")
        query = urlencode({"token": token})

        return f"{base_url}/#reset-password?{query}"
''',
)

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
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.services.event_tracking_service import EventTrackingService

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
        event_tracking_service=EventTrackingService(
            AnalyticsRepository(database),
        ),
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

write(
    "backend/app/api/v1/endpoints/auth.py",
    '''
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import get_settings
from app.db.mongodb import get_database
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from app.services.auth_service import (
    AuthService,
    DuplicateEmailError,
    InvalidCredentialsError,
    InvalidResetTokenError,
)
from app.services.email_service import EmailService
from app.services.event_tracking_service import EventTrackingService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(database=Depends(get_database)) -> AuthService:
    settings = get_settings()

    return AuthService(
        user_repository=UserRepository(database),
        profile_repository=ProfileRepository(database),
        password_reset_repository=PasswordResetRepository(database),
        email_service=EmailService(settings),
        event_tracking_service=EventTrackingService(
            AnalyticsRepository(database),
        ),
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        return await service.register(payload)
    except DuplicateEmailError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        ) from exc


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        return await service.login(
            email=str(payload.email),
            password=payload.password,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        ) from exc


@router.post("/token", response_model=AuthResponse)
async def swagger_oauth_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        return await service.login(
            email=form_data.username,
            password=form_data.password,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        ) from exc


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> ForgotPasswordResponse:
    return await service.forgot_password(str(payload.email))


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    payload: ResetPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> ResetPasswordResponse:
    try:
        return await service.reset_password(
            token=payload.token,
            new_password=payload.new_password,
        )
    except InvalidResetTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token is invalid, expired, or already used",
        ) from exc
''',
)

write(
    "backend/app/services/recommendation_service.py",
    '''
from app.algorithms.filters import apply_hard_filters
from app.algorithms.normalizer import normalized_request
from app.algorithms.routine_builder import build_routine
from app.algorithms.scoring import score_products
from app.algorithms.sorting import sort_scored_products
from app.core.enums import AnalyticsEventType
from app.core.time import utc_now
from app.repositories.product_repository import ProductRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.schemas.recommendation import (
    FilterSummary,
    RecommendationRequest,
    RecommendationResponse,
    RecommendationRoutine,
)
from app.services.event_tracking_service import EventTrackingService
from app.services.explanation_service import ExplanationService


class RecommendationService:
    algorithm_version = "rule-based-v1"

    def __init__(
        self,
        product_repository: ProductRepository,
        recommendation_repository: RecommendationRepository,
        explanation_service: ExplanationService,
        event_tracking_service: EventTrackingService | None = None,
    ) -> None:
        self.product_repository = product_repository
        self.recommendation_repository = recommendation_repository
        self.explanation_service = explanation_service
        self.event_tracking_service = event_tracking_service

    async def create_recommendation(
        self,
        request: RecommendationRequest,
        *,
        user_id: str | None = None,
        authenticated_anonymous_id: str | None = None,
    ) -> RecommendationResponse:
        normalized = normalized_request(request)
        session_anonymous_id = normalized.anonymous_id or authenticated_anonymous_id

        products = await self.product_repository.list_active_products()
        filter_result = apply_hard_filters(products=products, request=normalized)

        scored = score_products(filter_result.allowed_products, normalized)
        sorted_products = sort_scored_products(scored)

        routine_source = build_routine(
            products=sorted_products,
            experience=normalized.experience,
        )

        routine = RecommendationRoutine(
            morning=[
                self.explanation_service.build_recommended_product(item, normalized)
                for item in routine_source["morning"]
            ],
            evening=[
                self.explanation_service.build_recommended_product(item, normalized)
                for item in routine_source["evening"]
            ],
        )

        unique_products = {
            item.product.external_id: item.product
            for item in [*routine.morning, *routine.evening]
        }

        total_price_rub = sum(product.price_rub for product in unique_products.values())

        filter_summary = FilterSummary(
            total_products=len(products),
            allowed_products=len(filter_result.allowed_products),
            filtered_out=len(products) - len(filter_result.allowed_products),
            filter_reasons=filter_result.filter_reasons,
        )

        result_payload = {
            "algorithm_version": self.algorithm_version,
            "routine": routine.model_dump(),
            "filter_summary": filter_summary.model_dump(),
            "total_price_rub": total_price_rub,
            "created_at": utc_now(),
        }

        recommendation_id = await self.recommendation_repository.save_session(
            request=normalized.model_dump(),
            result=result_payload,
            algorithm_version=self.algorithm_version,
            anonymous_id=session_anonymous_id,
            user_id=user_id,
        )

        if self.event_tracking_service is not None:
            await self.event_tracking_service.record(
                AnalyticsEventType.QUESTIONNAIRE_COMPLETED,
                user_id=user_id,
                anonymous_id=session_anonymous_id,
                recommendation_id=recommendation_id,
                metadata={
                    "age_group": self._age_group(normalized.age),
                    "skin_type": normalized.skin_type,
                    "concerns": normalized.concerns,
                    "budget": normalized.budget,
                    "excluded_ingredients": normalized.excluded_ingredients,
                    "custom_restriction_count": len(normalized.custom_restrictions),
                    "experience": normalized.experience,
                    "values": normalized.values,
                },
            )

            await self.event_tracking_service.record(
                AnalyticsEventType.RECOMMENDATION_GENERATED,
                user_id=user_id,
                anonymous_id=session_anonymous_id,
                recommendation_id=recommendation_id,
                metadata={
                    "algorithm_version": self.algorithm_version,
                    "allowed_products": filter_summary.allowed_products,
                    "filtered_out": filter_summary.filtered_out,
                    "filter_reasons": filter_summary.filter_reasons,
                    "total_price_rub": total_price_rub,
                    "routine_product_count": len(unique_products),
                    "morning_count": len(routine.morning),
                    "evening_count": len(routine.evening),
                    "product_external_ids": sorted(unique_products),
                },
            )

        return RecommendationResponse(
            recommendation_id=recommendation_id,
            **result_payload,
        )

    async def get_recommendation(self, recommendation_id: str) -> RecommendationResponse | None:
        document = await self.recommendation_repository.find_by_id(recommendation_id)

        if document is None:
            return None

        return RecommendationResponse(
            recommendation_id=document["recommendation_id"],
            **document["result"],
        )

    @staticmethod
    def _age_group(age: int | None) -> str | None:
        if age is None:
            return None
        if age < 18:
            return "12-17"
        if age < 25:
            return "18-24"
        if age < 35:
            return "25-34"
        if age < 45:
            return "35-44"
        return "45+"
''',
)

write(
    "backend/app/api/v1/endpoints/recommendations.py",
    '''
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.dependencies import get_optional_current_user
from app.db.mongodb import get_database
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.services.event_tracking_service import EventTrackingService
from app.services.explanation_service import ExplanationService
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def get_recommendation_service(database=Depends(get_database)) -> RecommendationService:
    return RecommendationService(
        product_repository=ProductRepository(database),
        recommendation_repository=RecommendationRepository(database),
        explanation_service=ExplanationService(),
        event_tracking_service=EventTrackingService(
            AnalyticsRepository(database),
        ),
    )


@router.post("", response_model=RecommendationResponse)
async def create_recommendation(
    payload: RecommendationRequest,
    current_user: Annotated[dict | None, Depends(get_optional_current_user)],
    service: Annotated[RecommendationService, Depends(get_recommendation_service)],
) -> RecommendationResponse:
    return await service.create_recommendation(
        payload,
        user_id=current_user["user_id"] if current_user is not None else None,
        authenticated_anonymous_id=(
            current_user.get("anonymous_id") if current_user is not None else None
        ),
    )


@router.get("/{recommendation_id}", response_model=RecommendationResponse)
async def get_recommendation(
    recommendation_id: str,
    service: RecommendationService = Depends(get_recommendation_service),
) -> RecommendationResponse:
    recommendation = await service.get_recommendation(recommendation_id)

    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found",
        )

    return recommendation
''',
)

write(
    "backend/app/services/feedback_service.py",
    '''
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

        feedback = await self.feedback_repository.create(
            recommendation_id=recommendation_id,
            product_external_id=payload.product_external_id,
            reason=payload.reason,
            comment=payload.comment,
            anonymous_id=payload.anonymous_id,
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
        anonymous_id = recommendation.get("anonymous_id") or payload.anonymous_id
        candidate_ids = [
            candidate["product"]["external_id"]
            for candidate in candidates
            if candidate.get("product", {}).get("external_id")
        ]

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

        product = await self.database["products"].find_one(
            {"external_id": product_external_id}
        )

        if product is None:
            return None

        return {
            "product": product,
            "routine_step": product.get("routine_step"),
            "score": 0,
            "score_breakdown": {},
            "matched_concerns": [],
            "why_here": "",
        }

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
''',
)

write(
    "backend/app/services/replacement_service.py",
    '''
from typing import Any

from bson import ObjectId
from fastapi import HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase

from app.core.enums import AnalyticsEventType
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.replacement_repository import ReplacementRepository
from app.schemas.replacement import ReplacementSelectionResponse, ReplacementSessionResponse
from app.services.event_tracking_service import EventTrackingService


class ReplacementService:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.database = database
        self.repository = ReplacementRepository(database)
        self.event_tracking_service = EventTrackingService(
            AnalyticsRepository(database),
        )

    async def list_sessions(
        self,
        recommendation_id: str,
    ) -> list[ReplacementSessionResponse]:
        sessions = await self.repository.list_by_recommendation(recommendation_id)
        return [ReplacementSessionResponse(**session) for session in sessions]

    async def select_replacement(
        self,
        *,
        recommendation_id: str,
        session_id: str,
        product_external_id: str,
    ) -> ReplacementSelectionResponse:
        session = await self.repository.find_by_id(session_id)

        if session is None or session["recommendation_id"] != recommendation_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Replacement session not found",
            )

        candidate_ids = {
            candidate["product"]["external_id"]
            for candidate in session.get("replacement_candidates", [])
            if candidate.get("product", {}).get("external_id")
        }

        if product_external_id not in candidate_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected product is not part of replacement candidates",
            )

        updated = await self.repository.select(
            session_id=session_id,
            product_external_id=product_external_id,
        )

        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Replacement session not found",
            )

        identity = await self._recommendation_identity(recommendation_id)

        await self.event_tracking_service.record(
            AnalyticsEventType.REPLACEMENT_SELECTED,
            user_id=identity.get("user_id"),
            anonymous_id=identity.get("anonymous_id"),
            recommendation_id=recommendation_id,
            product_external_id=product_external_id,
            metadata={
                "replacement_session_id": session_id,
                "feedback_id": session.get("feedback_id"),
                "original_product_external_id": session.get(
                    "original_product_external_id"
                ),
                "reason": session.get("reason"),
            },
        )

        return ReplacementSelectionResponse(
            replacement_session_id=session_id,
            selected_product_external_id=product_external_id,
        )

    async def _recommendation_identity(
        self,
        recommendation_id: str,
    ) -> dict[str, Any]:
        queries: list[dict[str, Any]] = [
            {"recommendation_id": recommendation_id},
            {"session_id": recommendation_id},
        ]

        if ObjectId.is_valid(recommendation_id):
            queries.insert(0, {"_id": ObjectId(recommendation_id)})

        for query in queries:
            document = await self.database["recommendation_sessions"].find_one(
                query,
                {"user_id": 1, "anonymous_id": 1},
            )
            if document is not None:
                return {
                    "user_id": document.get("user_id"),
                    "anonymous_id": document.get("anonymous_id"),
                }

        return {"user_id": None, "anonymous_id": None}
''',
)

write(
    "backend/app/services/user_service.py",
    '''
from app.core.enums import AnalyticsEventType
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    QuestionnaireHistoryCreate,
    UserProfileResponse,
    UserProfileUpdate,
    UserResponse,
    UserUpdate,
)
from app.services.event_tracking_service import EventTrackingService


class UserService:
    def __init__(
        self,
        user_repository: UserRepository,
        profile_repository: ProfileRepository,
        event_tracking_service: EventTrackingService | None = None,
    ) -> None:
        self.user_repository = user_repository
        self.profile_repository = profile_repository
        self.event_tracking_service = event_tracking_service

    async def get_me(self, user: dict) -> UserResponse:
        return UserResponse(**user)

    async def update_me(
        self,
        user: dict,
        payload: UserUpdate,
    ) -> UserResponse | None:
        updated = await self.user_repository.update_user(
            user_id=user["user_id"],
            full_name=payload.full_name,
            anonymous_id=payload.anonymous_id,
        )

        if updated is None:
            return None

        await self.profile_repository.sync_anonymous_id(
            user_id=updated["user_id"],
            anonymous_id=updated.get("anonymous_id"),
        )

        return UserResponse(**updated)

    async def get_my_profile(self, user: dict) -> UserProfileResponse:
        profile = await self.profile_repository.ensure_profile(
            user_id=user["user_id"],
            anonymous_id=user.get("anonymous_id"),
        )

        return UserProfileResponse(**profile)

    async def update_my_profile(
        self,
        user: dict,
        payload: UserProfileUpdate,
    ) -> UserProfileResponse | None:
        profile = await self.profile_repository.ensure_profile(
            user_id=user["user_id"],
            anonymous_id=user.get("anonymous_id"),
        )

        payload_data = payload.model_dump()
        updated = await self.profile_repository.update_profile(
            user_id=profile["user_id"],
            payload=payload_data,
        )

        if updated is None:
            return None

        if self.event_tracking_service is not None:
            fields_updated = sorted(
                key for key, value in payload_data.items() if value is not None
            )
            await self.event_tracking_service.record(
                AnalyticsEventType.PROFILE_SAVED,
                user_id=user["user_id"],
                anonymous_id=user.get("anonymous_id"),
                metadata={
                    "source": "profile_update",
                    "fields_updated": fields_updated,
                    "skin_type": updated.get("skin_type"),
                    "concern_count": len(updated.get("concerns") or []),
                    "restriction_count": len(
                        [
                            *(updated.get("excluded_ingredients") or []),
                            *(updated.get("custom_restrictions") or []),
                        ]
                    ),
                },
            )

        return UserProfileResponse(**updated)

    async def append_questionnaire_history(
        self,
        user: dict,
        payload: QuestionnaireHistoryCreate,
    ) -> UserProfileResponse | None:
        profile = await self.profile_repository.ensure_profile(
            user_id=user["user_id"],
            anonymous_id=user.get("anonymous_id"),
        )

        updated = await self.profile_repository.append_questionnaire_history(
            user_id=profile["user_id"],
            entry=payload.model_dump(),
        )

        if updated is None:
            return None

        if self.event_tracking_service is not None:
            await self.event_tracking_service.record(
                AnalyticsEventType.PROFILE_SAVED,
                user_id=user["user_id"],
                anonymous_id=user.get("anonymous_id"),
                recommendation_id=payload.recommendation_id,
                metadata={
                    "source": "questionnaire_history",
                    "history_size": len(updated.get("questionnaire_history") or []),
                },
            )

        return UserProfileResponse(**updated)
''',
)

write(
    "backend/app/api/v1/endpoints/users.py",
    '''
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.dependencies import get_current_user
from app.db.mongodb import get_database
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    QuestionnaireHistoryCreate,
    UserProfileResponse,
    UserProfileUpdate,
    UserResponse,
    UserUpdate,
)
from app.services.event_tracking_service import EventTrackingService
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(database=Depends(get_database)) -> UserService:
    return UserService(
        user_repository=UserRepository(database),
        profile_repository=ProfileRepository(database),
        event_tracking_service=EventTrackingService(
            AnalyticsRepository(database),
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await service.get_me(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    payload: UserUpdate,
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    result = await service.update_me(
        user=current_user,
        payload=payload,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return result


@router.get("/me/profile", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserProfileResponse:
    return await service.get_my_profile(current_user)


@router.patch("/me/profile", response_model=UserProfileResponse)
async def update_my_profile(
    payload: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserProfileResponse:
    result = await service.update_my_profile(
        user=current_user,
        payload=payload,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    return result


@router.post("/me/profile/questionnaire-history", response_model=UserProfileResponse)
async def append_questionnaire_history(
    payload: QuestionnaireHistoryCreate,
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserProfileResponse:
    result = await service.append_questionnaire_history(
        user=current_user,
        payload=payload,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    return result
''',
)

write(
    "backend/app/services/llm_explanation_service.py",
    '''
from openai import AsyncOpenAI

from app.core.config import get_settings
from app.core.enums import AnalyticsEventType
from app.llm.prompt_templates import KOYASH_EXPLANATION_SYSTEM_PROMPT, build_user_prompt
from app.schemas.llm import LLMExplanationPreviewRequest, LLMExplanationPreviewResponse
from app.services.event_tracking_service import EventTrackingService


FUNCTION_HINTS = {
    "глицерин": "увлажняющий",
    "glycerin": "увлажняющий",
    "пантенол": "успокаивающий",
    "panthenol": "успокаивающий",
    "ниацинамид": "себорегулирующий",
    "niacinamide": "себорегулирующий",
    "цинк": "себорегулирующий",
    "zinc": "себорегулирующий",
    "аминокислотные пав": "очищающий",
    "amino acid surfactants": "очищающий",
    "гиалуроновая кислота": "увлажняющий",
    "hyaluronic acid": "увлажняющий",
    "centella": "успокаивающий",
    "центелла": "успокаивающий",
}


class LLMExplanationService:
    def __init__(
        self,
        event_tracking_service: EventTrackingService | None = None,
    ) -> None:
        self.settings = get_settings()
        self.event_tracking_service = event_tracking_service

    def _ingredient_function(self, ingredients: list[str]) -> tuple[str, str]:
        if not ingredients:
            return "состав", "базовой функцией ухода"

        first = ingredients[0]

        for ingredient in ingredients:
            key = ingredient.lower()
            for pattern, function in FUNCTION_HINTS.items():
                if pattern in key:
                    return ingredient, function

        return first, "базовой функцией ухода"

    def _fallback_explanation(self, payload: LLMExplanationPreviewRequest) -> str:
        ingredient, function = self._ingredient_function(payload.ingredients)

        if payload.concern_match <= 0:
            text = (
                f"{payload.name} закрывает шаг «{payload.step}». "
                f"{ingredient} в уходе связывают с {function} функцией."
            )
        else:
            text = (
                f"{payload.name} добавлен из-за совпадения с запросом. "
                f"{ingredient} - известный {function} компонент."
            )

        return text[:200]

    def _build_prompts(self, payload: LLMExplanationPreviewRequest) -> tuple[str, str]:
        user_prompt = build_user_prompt(
            skin_type=payload.skin_type,
            concerns=payload.concerns,
            name=payload.name,
            brand=payload.brand,
            step=payload.step,
            ingredients=payload.ingredients,
            concern_match=payload.concern_match,
        )

        return KOYASH_EXPLANATION_SYSTEM_PROMPT, user_prompt

    async def preview(
        self,
        payload: LLMExplanationPreviewRequest,
        *,
        user_id: str | None = None,
        anonymous_id: str | None = None,
    ) -> LLMExplanationPreviewResponse:
        system_prompt, user_prompt = self._build_prompts(payload)

        fallback_reason = self._fallback_reason(payload)
        if fallback_reason is not None:
            await self._record_result(
                event_type=AnalyticsEventType.LLM_EXPLANATION_FALLBACK,
                payload=payload,
                user_id=user_id,
                anonymous_id=anonymous_id,
                metadata={"fallback_reason": fallback_reason},
            )
            return self._fallback_response(payload, system_prompt, user_prompt)

        client = AsyncOpenAI(
            api_key=self.settings.vsellm_api_key,
            base_url=self.settings.vsellm_base_url,
            timeout=self.settings.llm_timeout_seconds,
        )

        try:
            response = await client.chat.completions.create(
                model=self.settings.vsellm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=120,
            )
        except Exception as exc:
            await self._record_result(
                event_type=AnalyticsEventType.LLM_EXPLANATION_FALLBACK,
                payload=payload,
                user_id=user_id,
                anonymous_id=anonymous_id,
                metadata={
                    "fallback_reason": "provider_error",
                    "error_type": type(exc).__name__,
                },
            )
            return self._fallback_response(payload, system_prompt, user_prompt)

        explanation = (response.choices[0].message.content or "").strip()[:200]

        await self._record_result(
            event_type=AnalyticsEventType.LLM_EXPLANATION_SUCCESS,
            payload=payload,
            user_id=user_id,
            anonymous_id=anonymous_id,
            metadata={"provider": "vsellm"},
        )

        return LLMExplanationPreviewResponse(
            used_llm=True,
            provider="vsellm",
            model=self.settings.vsellm_model,
            explanation=explanation,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    def _fallback_reason(self, payload: LLMExplanationPreviewRequest) -> str | None:
        if not payload.use_llm:
            return "llm_not_requested"
        if not self.settings.llm_enabled:
            return "llm_disabled"
        if not self.settings.vsellm_api_key:
            return "api_key_missing"
        return None

    def _fallback_response(
        self,
        payload: LLMExplanationPreviewRequest,
        system_prompt: str,
        user_prompt: str,
    ) -> LLMExplanationPreviewResponse:
        return LLMExplanationPreviewResponse(
            used_llm=False,
            provider="deterministic-fallback",
            model=self.settings.vsellm_model,
            explanation=self._fallback_explanation(payload),
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    async def _record_result(
        self,
        *,
        event_type: AnalyticsEventType,
        payload: LLMExplanationPreviewRequest,
        user_id: str | None,
        anonymous_id: str | None,
        metadata: dict,
    ) -> None:
        if self.event_tracking_service is None:
            return

        await self.event_tracking_service.record(
            event_type,
            user_id=user_id,
            anonymous_id=anonymous_id,
            metadata={
                **metadata,
                "provider": self.settings.llm_provider,
                "model": self.settings.vsellm_model,
                "step": payload.step,
                "concern_match": payload.concern_match,
                "ingredient_count": len(payload.ingredients),
                "requested_llm": payload.use_llm,
            },
        )

    def demo_payloads(self) -> list[LLMExplanationPreviewRequest]:
        return [
            LLMExplanationPreviewRequest(
                skin_type="combination",
                concerns=["acne", "sebum"],
                name="Gentle Balance Cleanser",
                brand="Koyash Sample",
                step="cleanser",
                ingredients=["amino acid surfactants", "glycerin", "panthenol"],
                concern_match=0,
                use_llm=False,
            ),
            LLMExplanationPreviewRequest(
                skin_type="oily",
                concerns=["sebum"],
                name="Sebum Calm Serum",
                brand="Koyash Sample",
                step="serum",
                ingredients=["niacinamide", "zinc", "glycerin"],
                concern_match=1,
                use_llm=False,
            ),
            LLMExplanationPreviewRequest(
                skin_type="sensitive",
                concerns=["sensitivity", "dryness"],
                name="Barrier Comfort Cream",
                brand="Koyash Sample",
                step="moisturizer",
                ingredients=["panthenol", "glycerin", "centella"],
                concern_match=2,
                use_llm=False,
            ),
        ]
''',
)

write(
    "backend/app/api/v1/endpoints/llm_explanations.py",
    '''
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_optional_current_user
from app.db.mongodb import get_database
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.llm import (
    LLMDemoPayloadsResponse,
    LLMExplanationPreviewRequest,
    LLMExplanationPreviewResponse,
)
from app.services.event_tracking_service import EventTrackingService
from app.services.llm_explanation_service import LLMExplanationService

router = APIRouter(prefix="/llm/explanations", tags=["llm explanations"])


def get_llm_explanation_service(database=Depends(get_database)) -> LLMExplanationService:
    return LLMExplanationService(
        event_tracking_service=EventTrackingService(
            AnalyticsRepository(database),
        ),
    )


@router.get("/demo-payloads", response_model=LLMDemoPayloadsResponse)
async def demo_payloads() -> LLMDemoPayloadsResponse:
    service = LLMExplanationService()
    return LLMDemoPayloadsResponse(payloads=service.demo_payloads())


@router.post("/preview", response_model=LLMExplanationPreviewResponse)
async def preview_explanation(
    payload: LLMExplanationPreviewRequest,
    current_user: Annotated[dict | None, Depends(get_optional_current_user)],
    service: Annotated[LLMExplanationService, Depends(get_llm_explanation_service)],
) -> LLMExplanationPreviewResponse:
    return await service.preview(
        payload,
        user_id=current_user["user_id"] if current_user is not None else None,
        anonymous_id=(
            current_user.get("anonymous_id") if current_user is not None else None
        ),
    )
''',
)

write(
    "backend/app/db/indexes.py",
    '''
from typing import Any

from pymongo import ASCENDING, DESCENDING
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import OperationFailure


async def _create_index_safely(
    collection: Any,
    keys: Any,
    **kwargs: Any,
) -> None:
    try:
        await collection.create_index(keys, **kwargs)
    except OperationFailure as exc:
        if getattr(exc, "code", None) == 86:
            return
        raise


async def create_indexes(database: AsyncDatabase, analytics_ttl_days: int) -> None:
    ttl_seconds = analytics_ttl_days * 24 * 60 * 60

    await _create_index_safely(database["users"], "email", unique=True)
    await _create_index_safely(database["users"], "role")
    await _create_index_safely(database["users"], "created_at")
    await _create_index_safely(database["user_profiles"], "user_id", unique=True)

    await _create_index_safely(database["products"], "external_id", unique=True)
    await _create_index_safely(database["products"], [("is_active", ASCENDING), ("routine_step", ASCENDING)])
    await _create_index_safely(database["products"], [("category", ASCENDING), ("budget_segment", ASCENDING)])

    await _create_index_safely(database["ingredient_aliases"], "canonical_key", unique=True)
    await _create_index_safely(database["restriction_suggestions"], "canonical_key", unique=True)
    await _create_index_safely(
        database["restriction_suggestions"],
        [("status", ASCENDING), ("usage_count", DESCENDING)],
    )

    await _create_index_safely(database["custom_restriction_events"], "normalized_key")
    await _create_index_safely(database["custom_restriction_events"], "created_at")

    await _create_index_safely(database["recommendation_sessions"], "user_id")
    await _create_index_safely(database["recommendation_sessions"], "anonymous_id")
    await _create_index_safely(database["recommendation_sessions"], "created_at")

    await _create_index_safely(database["feedback_events"], "recommendation_id")
    await _create_index_safely(database["feedback_events"], "product_external_id")
    await _create_index_safely(database["feedback_events"], "reason")
    await _create_index_safely(database["feedback_events"], "created_at")
    await _create_index_safely(
        database["feedback_events"],
        [("reason", ASCENDING), ("created_at", DESCENDING)],
    )

    await _create_index_safely(database["replacement_sessions"], "recommendation_id")
    await _create_index_safely(database["replacement_sessions"], "feedback_id")
    await _create_index_safely(database["replacement_sessions"], "created_at")
    await _create_index_safely(database["replacement_sessions"], "selected_product_external_id")

    await _create_index_safely(database["analytics_events"], "event_type")
    await _create_index_safely(database["analytics_events"], "event_source")
    await _create_index_safely(database["analytics_events"], "recommendation_id")
    await _create_index_safely(database["analytics_events"], "product_external_id")
    await _create_index_safely(database["analytics_events"], "created_at", expireAfterSeconds=ttl_seconds)
    await _create_index_safely(
        database["analytics_events"],
        [("event_type", ASCENDING), ("created_at", DESCENDING)],
    )
    await _create_index_safely(
        database["analytics_events"],
        [("event_source", ASCENDING), ("event_type", ASCENDING), ("created_at", DESCENDING)],
    )
    await _create_index_safely(database["analytics_events"], "anonymous_id")
    await _create_index_safely(database["analytics_events"], "user_id")

    await _create_index_safely(
        database["analytics_daily_metrics"],
        [("date", ASCENDING), ("metric", ASCENDING)],
    )

    await _create_index_safely(database["llm_explanation_logs"], "recommendation_id")
    await _create_index_safely(database["llm_explanation_logs"], "created_at")

    await _create_index_safely(database["password_reset_tokens"], "token_hash", unique=True)
    await _create_index_safely(database["password_reset_tokens"], "user_id")
    await _create_index_safely(database["password_reset_tokens"], "expires_at", expireAfterSeconds=0)
    await _create_index_safely(database["password_reset_tokens"], "used_at")
''',
)

write(
    "backend/tests/test_server_event_tracking.py",
    '''
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pymongo import DESCENDING, MongoClient

from app.core.config import get_settings
from app.core.enums import AnalyticsEventType
from app.main import app
from app.services.event_tracking_service import EventTrackingService


def _register(client: TestClient) -> tuple[str, dict]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"events-{uuid4().hex}@example.com",
            "password": "StrongPassword123!",
            "full_name": "Event Test User",
            "anonymous_id": f"anon-{uuid4().hex}",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    return payload["access_token"], payload["user"]


def _recommendation_payload(anonymous_id: str) -> dict:
    return {
        "age": 24,
        "skin_type": "combination",
        "concerns": ["sebum", "acne"],
        "budget": "balanced",
        "excluded_ingredients": ["fragrance"],
        "custom_restrictions": [],
        "experience": "guided",
        "values": ["comfort", "price_quality"],
        "anonymous_id": anonymous_id,
    }


def _find_event(query: dict) -> dict | None:
    settings = get_settings()
    client = MongoClient(
        settings.mongo_uri,
        uuidRepresentation="standard",
        serverSelectionTimeoutMS=5000,
    )
    try:
        return client[settings.mongo_db_name]["analytics_events"].find_one(
            query,
            sort=[("created_at", DESCENDING)],
        )
    finally:
        client.close()


def test_registration_is_recorded_as_server_event_without_email_metadata() -> None:
    with TestClient(app) as client:
        _, user = _register(client)

    event = _find_event(
        {
            "event_type": AnalyticsEventType.REGISTRATION_COMPLETED.value,
            "event_source": "server",
            "user_id": user["user_id"],
        }
    )

    assert event is not None
    assert event["metadata"]["name_provided"] is True
    assert "email" not in event["metadata"]
    assert "password" not in event["metadata"]


def test_authenticated_recommendation_records_questionnaire_and_result_events() -> None:
    with TestClient(app) as client:
        token, user = _register(client)
        response = client.post(
            "/api/v1/recommendations",
            headers={"Authorization": f"Bearer {token}"},
            json=_recommendation_payload(user["anonymous_id"]),
        )

    assert response.status_code == 200
    recommendation_id = response.json()["recommendation_id"]

    questionnaire_event = _find_event(
        {
            "event_type": AnalyticsEventType.QUESTIONNAIRE_COMPLETED.value,
            "event_source": "server",
            "recommendation_id": recommendation_id,
        }
    )
    recommendation_event = _find_event(
        {
            "event_type": AnalyticsEventType.RECOMMENDATION_GENERATED.value,
            "event_source": "server",
            "recommendation_id": recommendation_id,
        }
    )

    assert questionnaire_event is not None
    assert questionnaire_event["user_id"] == user["user_id"]
    assert questionnaire_event["metadata"]["skin_type"] == "combination"
    assert recommendation_event is not None
    assert recommendation_event["metadata"]["routine_product_count"] >= 1
    assert recommendation_event["metadata"]["product_external_ids"]


def test_feedback_generation_and_selection_are_recorded_server_side() -> None:
    with TestClient(app) as client:
        token, user = _register(client)
        recommendation_response = client.post(
            "/api/v1/recommendations",
            headers={"Authorization": f"Bearer {token}"},
            json=_recommendation_payload(user["anonymous_id"]),
        )
        assert recommendation_response.status_code == 200
        recommendation = recommendation_response.json()
        original = recommendation["routine"]["morning"][0]["product"]

        feedback_response = client.post(
            f"/api/v1/recommendations/{recommendation['recommendation_id']}/feedback",
            json={
                "product_external_id": original["external_id"],
                "reason": "dislikes_brand",
                "comment": "This comment must not enter analytics metadata",
                "anonymous_id": user["anonymous_id"],
            },
        )
        assert feedback_response.status_code == 200
        feedback = feedback_response.json()
        assert 1 <= len(feedback["replacement_candidates"]) <= 3

        selected_product_id = feedback["replacement_candidates"][0]["product"]["external_id"]
        selection_response = client.post(
            "/api/v1/recommendations/"
            f"{recommendation['recommendation_id']}/replacements/"
            f"{feedback['replacement_session_id']}/select",
            json={"product_external_id": selected_product_id},
        )

    assert selection_response.status_code == 200

    feedback_event = _find_event(
        {
            "event_type": AnalyticsEventType.FEEDBACK_SUBMITTED.value,
            "event_source": "server",
            "recommendation_id": recommendation["recommendation_id"],
        }
    )
    generated_event = _find_event(
        {
            "event_type": AnalyticsEventType.REPLACEMENT_GENERATED.value,
            "event_source": "server",
            "recommendation_id": recommendation["recommendation_id"],
        }
    )
    selected_event = _find_event(
        {
            "event_type": AnalyticsEventType.REPLACEMENT_SELECTED.value,
            "event_source": "server",
            "recommendation_id": recommendation["recommendation_id"],
            "product_external_id": selected_product_id,
        }
    )

    assert feedback_event is not None
    assert feedback_event["metadata"]["reason"] == "dislikes_brand"
    assert "comment" not in feedback_event["metadata"]
    assert generated_event is not None
    assert 1 <= generated_event["metadata"]["candidate_count"] <= 3
    assert selected_event is not None
    assert selected_event["metadata"]["replacement_session_id"] == feedback[
        "replacement_session_id"
    ]


def test_profile_update_is_recorded_without_personal_profile_values() -> None:
    with TestClient(app) as client:
        token, user = _register(client)
        response = client.patch(
            "/api/v1/users/me/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "skin_type": "dry",
                "concerns": ["dryness"],
                "budget": "balanced",
            },
        )

    assert response.status_code == 200
    event = _find_event(
        {
            "event_type": AnalyticsEventType.PROFILE_SAVED.value,
            "event_source": "server",
            "user_id": user["user_id"],
            "metadata.source": "profile_update",
        }
    )

    assert event is not None
    assert event["metadata"]["skin_type"] == "dry"
    assert "full_name" not in event["metadata"]
    assert "email" not in event["metadata"]


def test_llm_fallback_is_recorded_by_backend() -> None:
    with TestClient(app) as client:
        token, user = _register(client)
        response = client.post(
            "/api/v1/llm/explanations/preview",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "skin_type": "combination",
                "concerns": ["acne"],
                "name": "Dataset Product",
                "brand": "Dataset Brand",
                "step": "serum",
                "ingredients": ["niacinamide"],
                "concern_match": 1,
                "use_llm": False,
            },
        )

    assert response.status_code == 200
    assert response.json()["used_llm"] is False

    event = _find_event(
        {
            "event_type": AnalyticsEventType.LLM_EXPLANATION_FALLBACK.value,
            "event_source": "server",
            "user_id": user["user_id"],
            "metadata.step": "serum",
        }
    )

    assert event is not None
    assert event["metadata"]["fallback_reason"] == "llm_not_requested"
    assert "user_prompt" not in event["metadata"]
    assert "system_prompt" not in event["metadata"]


def test_questionnaire_completed_cannot_be_spoofed_via_public_endpoint() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/analytics/events",
            json={
                "event_type": "questionnaire_completed",
                "anonymous_id": "spoof-attempt",
                "metadata": {},
            },
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_analytics_failure_does_not_break_business_flow() -> None:
    class FailingRepository:
        async def save_event(self, **kwargs):
            raise RuntimeError("analytics unavailable")

    tracker = EventTrackingService(FailingRepository())

    result = await tracker.record(
        AnalyticsEventType.PROFILE_SAVED,
        user_id="test-user",
        metadata={"source": "unit-test"},
    )

    assert result is None
''',
)

write(
    "docs/analytics-event-contract.md",
    '''
# KOYASH analytics event contract

## Trust boundary

Analytics events have an explicit `event_source`:

- `public` — UI interaction events accepted from the browser through `/api/v1/analytics/events`;
- `server` — domain events emitted only by backend services after the operation succeeds.

Dashboard conversion and business metrics must use server-owned events or source domain collections. A browser event must never be treated as proof that registration, recommendation, feedback, replacement selection, or an LLM request succeeded.

## Server-owned events

- `registration_completed`
- `questionnaire_completed`
- `recommendation_generated`
- `feedback_submitted`
- `replacement_generated`
- `replacement_selected`
- `profile_saved`
- `llm_explanation_success`
- `llm_explanation_fallback`

## Public UI events

- `questionnaire_opened`
- `questionnaire_started`
- `question_answered`
- `result_viewed`
- `product_viewed`
- `product_details_opened`

## Data minimization

Server analytics metadata must not contain:

- email;
- full name;
- phone;
- password;
- access/reset tokens;
- authorization headers;
- feedback comment text;
- prompts or LLM API credentials.

Exact user and anonymous identifiers may remain in raw MongoDB event documents for attribution, but admin responses must not expose those identifiers directly.

## Reliability

Analytics writes are best-effort. A temporary analytics failure must not break registration, recommendation generation, feedback submission, replacement selection, profile saving, or deterministic LLM fallback.
''',
)

print("STEP 4.9B APPLIED")
print("- server-owned events have event_source=server")
print("- public UI events have event_source=public")
print("- registration/recommendation/feedback/replacements/profile/LLM are tracked")
print("- analytics failures do not break product flows")
print("- comments, email, passwords, tokens, and prompts are excluded from metadata")
