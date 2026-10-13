from pathlib import Path

ROOT = Path(r"C:\Projects\sunwise-koyash")


def write_file(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip("\n"), encoding="utf-8")


def append_env_example() -> None:
    path = ROOT / "backend/.env.example"
    text = path.read_text(encoding="utf-8") if path.exists() else ""

    additions = {
        "FRONTEND_BASE_URL": "http://localhost:8080",
        "PASSWORD_RESET_TOKEN_EXPIRE_MINUTES": "30",
        "SMTP_ENABLED": "false",
        "SMTP_HOST": "",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "",
        "SMTP_PASSWORD": "",
        "SMTP_FROM_EMAIL": "no-reply@koyash.local",
        "SMTP_FROM_NAME": "KOYASH",
    }

    for key, value in additions.items():
        if f"{key}=" not in text:
            text += f"\n{key}={value}"

    path.write_text(text.strip() + "\n", encoding="utf-8")


write_file("backend/app/db/indexes.py", r'''
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
        # MongoDB raises IndexKeySpecsConflict when an existing index has the
        # same generated name but a slightly different spec. In local/dev DBs
        # this can happen after schema iterations. We do not want app startup
        # to crash because of an old local index.
        if getattr(exc, "code", None) == 86:
            return
        raise


async def create_indexes(database: AsyncDatabase, analytics_ttl_days: int) -> None:
    ttl_seconds = analytics_ttl_days * 24 * 60 * 60

    await _create_index_safely(database["users"], "email", unique=True)
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

    await _create_index_safely(database["replacement_sessions"], "recommendation_id")
    await _create_index_safely(database["replacement_sessions"], "feedback_id")

    await _create_index_safely(database["analytics_events"], "event_type")
    await _create_index_safely(database["analytics_events"], "created_at", expireAfterSeconds=ttl_seconds)
    await _create_index_safely(
        database["analytics_events"],
        [("event_type", ASCENDING), ("created_at", DESCENDING)],
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
''')


write_file("backend/app/repositories/password_reset_repository.py", r'''
from datetime import datetime
from typing import Any

from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase

from app.core.time import utc_now


def _clean(document: dict[str, Any]) -> dict[str, Any]:
    document["reset_id"] = str(document.pop("_id"))
    return document


class PasswordResetRepository:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.collection = database["password_reset_tokens"]

    async def create_token(
        self,
        user_id: str,
        email: str,
        token_hash: str,
        expires_at: datetime,
    ) -> dict[str, Any]:
        now = utc_now()

        document = {
            "user_id": user_id,
            "email": email.lower(),
            "token_hash": token_hash,
            "expires_at": expires_at,
            "used_at": None,
            "created_at": now,
        }

        result = await self.collection.insert_one(document)
        document["_id"] = result.inserted_id

        return _clean(document)

    async def find_valid_by_hash(self, token_hash: str) -> dict[str, Any] | None:
        document = await self.collection.find_one(
            {
                "token_hash": token_hash,
                "used_at": None,
                "expires_at": {"$gt": utc_now()},
            }
        )

        if document is None:
            return None

        return _clean(document)

    async def mark_used(self, reset_id: str) -> bool:
        if not ObjectId.is_valid(reset_id):
            return False

        result = await self.collection.update_one(
            {"_id": ObjectId(reset_id), "used_at": None},
            {"$set": {"used_at": utc_now()}},
        )

        return result.modified_count == 1

    async def invalidate_user_tokens(self, user_id: str) -> None:
        await self.collection.update_many(
            {"user_id": user_id, "used_at": None},
            {"$set": {"used_at": utc_now()}},
        )
''')


write_file("backend/app/services/email_service.py", r'''
import asyncio
import smtplib
from email.message import EmailMessage

from app.core.config import Settings


class EmailService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def send_password_reset_email(
        self,
        to_email: str,
        reset_url: str,
    ) -> bool:
        if not self.settings.smtp_enabled:
            return False

        if not self.settings.smtp_host:
            return False

        return await asyncio.to_thread(
            self._send_password_reset_email_sync,
            to_email,
            reset_url,
        )

    def _send_password_reset_email_sync(
        self,
        to_email: str,
        reset_url: str,
    ) -> bool:
        message = EmailMessage()
        message["Subject"] = "Сброс пароля KOYASH"
        message["From"] = f"{self.settings.smtp_from_name} <{self.settings.smtp_from_email}>"
        message["To"] = to_email

        message.set_content(
            "\n".join(
                [
                    "Здравствуйте!",
                    "",
                    "Вы запросили сброс пароля для аккаунта KOYASH.",
                    "Чтобы задать новый пароль, откройте ссылку:",
                    "",
                    reset_url,
                    "",
                    "Ссылка действует ограниченное время и может быть использована только один раз.",
                    "",
                    "Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.",
                    "",
                    "KOYASH",
                ]
            )
        )

        try:
            if self.settings.smtp_port == 465:
                with smtplib.SMTP_SSL(
                    self.settings.smtp_host,
                    self.settings.smtp_port,
                    timeout=15,
                ) as smtp:
                    self._login_if_needed(smtp)
                    smtp.send_message(message)
            else:
                with smtplib.SMTP(
                    self.settings.smtp_host,
                    self.settings.smtp_port,
                    timeout=15,
                ) as smtp:
                    smtp.starttls()
                    self._login_if_needed(smtp)
                    smtp.send_message(message)
        except Exception:
            return False

        return True

    def _login_if_needed(self, smtp: smtplib.SMTP) -> None:
        if self.settings.smtp_username and self.settings.smtp_password:
            smtp.login(
                self.settings.smtp_username,
                self.settings.smtp_password,
            )
''')


write_file("backend/app/core/config.py", r'''
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="KOYASH API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")

    mongo_uri: str = Field(alias="MONGO_URI")
    mongo_db_name: str = Field(default="koyash", alias="MONGO_DB_NAME")

    cors_origins: str = Field(default="", alias="CORS_ORIGINS")

    jwt_secret_key: str = Field(default="change_me", alias="JWT_SECRET_KEY")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    analytics_raw_event_ttl_days: int = Field(default=180, alias="ANALYTICS_RAW_EVENT_TTL_DAYS")

    frontend_base_url: str = Field(default="http://localhost:8080", alias="FRONTEND_BASE_URL")
    password_reset_token_expire_minutes: int = Field(
        default=30,
        alias="PASSWORD_RESET_TOKEN_EXPIRE_MINUTES",
    )

    smtp_enabled: bool = Field(default=False, alias="SMTP_ENABLED")
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: str | None = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from_email: str = Field(default="no-reply@koyash.local", alias="SMTP_FROM_EMAIL")
    smtp_from_name: str = Field(default="KOYASH", alias="SMTP_FROM_NAME")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        if not self.cors_origins:
            return []
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
''')


write_file("backend/app/core/security.py", r'''
import hashlib
import hmac
import secrets
from datetime import timedelta
from typing import Any

import jwt
from jwt import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import get_settings
from app.core.time import utc_now

ALGORITHM = "HS256"
password_hash = PasswordHash.recommended()


def create_password_hash(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    expire = utc_now() + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )

    payload = {
        "sub": subject,
        "exp": expire,
        "type": "access",
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    settings = get_settings()

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
    except InvalidTokenError:
        return None

    if payload.get("type") != "access":
        return None

    return payload


def decode_token(token: str) -> dict[str, Any] | None:
    return decode_access_token(token)


def create_secure_token() -> str:
    return secrets.token_urlsafe(48)


def hash_password_reset_token(token: str) -> str:
    settings = get_settings()

    return hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
''')


write_file("backend/app/schemas/auth.py", r'''
from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserProfileResponse, UserResponse


class RegisterRequest(BaseModel):
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
''')


write_file("backend/app/repositories/user_repository.py", r'''
from typing import Any

from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase

from app.core.time import utc_now


def _clean_user(document: dict[str, Any], include_password_hash: bool = False) -> dict[str, Any]:
    document["user_id"] = str(document.pop("_id"))

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
''')


write_file("backend/app/services/auth_service.py", r'''
from datetime import timedelta
from urllib.parse import urlencode

from app.core.config import get_settings
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
    ) -> None:
        self.user_repository = user_repository
        self.profile_repository = profile_repository
        self.password_reset_repository = password_reset_repository
        self.email_service = email_service

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
''')


write_file("backend/app/api/v1/endpoints/auth.py", r'''
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import get_settings
from app.db.mongodb import get_database
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

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(database=Depends(get_database)) -> AuthService:
    settings = get_settings()

    return AuthService(
        user_repository=UserRepository(database),
        profile_repository=ProfileRepository(database),
        password_reset_repository=PasswordResetRepository(database),
        email_service=EmailService(settings),
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
''')


write_file("backend/tests/test_password_reset.py", r'''
from uuid import uuid4
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from app.main import app


def _email() -> str:
    return f"reset-{uuid4().hex}@example.com"


def _register(client: TestClient, email: str, password: str = "StrongPassword123!") -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Reset User",
            "anonymous_id": "password-reset-test",
        },
    )

    assert response.status_code == 201


def _extract_token(reset_url: str) -> str:
    parsed = urlparse(reset_url)
    fragment = parsed.fragment
    query = fragment.split("?", 1)[1] if "?" in fragment else parsed.query
    values = parse_qs(query)

    return values["token"][0]


def test_forgot_password_unknown_email_does_not_reveal_account() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": _email()},
        )

    assert response.status_code == 200
    payload = response.json()
    assert "Если аккаунт существует" in payload["message"]
    assert payload["dev_reset_url"] is None


def test_forgot_password_existing_user_returns_dev_reset_url() -> None:
    email = _email()

    with TestClient(app) as client:
        _register(client, email)

        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": email},
        )

    assert response.status_code == 200
    payload = response.json()
    assert "Если аккаунт существует" in payload["message"]
    assert payload["dev_reset_url"]
    assert "token=" in payload["dev_reset_url"]


def test_reset_password_changes_password_and_old_password_stops_working() -> None:
    email = _email()
    old_password = "StrongPassword123!"
    new_password = "NewStrongPassword123!"

    with TestClient(app) as client:
        _register(client, email, old_password)

        forgot_response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": email},
        )
        assert forgot_response.status_code == 200

        token = _extract_token(forgot_response.json()["dev_reset_url"])

        reset_response = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": token,
                "new_password": new_password,
            },
        )

        assert reset_response.status_code == 200
        assert reset_response.json()["message"] == "Пароль успешно обновлён."

        old_login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": old_password,
            },
        )

        new_login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": new_password,
            },
        )

    assert old_login_response.status_code == 401
    assert new_login_response.status_code == 200


def test_reset_token_cannot_be_reused() -> None:
    email = _email()

    with TestClient(app) as client:
        _register(client, email)

        forgot_response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": email},
        )
        assert forgot_response.status_code == 200

        token = _extract_token(forgot_response.json()["dev_reset_url"])

        first_reset = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": token,
                "new_password": "NewStrongPassword123!",
            },
        )

        second_reset = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": token,
                "new_password": "AnotherStrongPassword123!",
            },
        )

    assert first_reset.status_code == 200
    assert second_reset.status_code == 400


def test_reset_password_rejects_invalid_token() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "invalid-token-invalid-token-invalid-token",
                "new_password": "NewStrongPassword123!",
            },
        )

    assert response.status_code == 400
''')


append_env_example()

print("Step 4.1 password reset repair finished successfully.")