from pathlib import Path

ROOT = Path(r"C:\Projects\sunwise-koyash")


def write_file(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip("\n"), encoding="utf-8")


write_file("backend/app/core/security.py", r"""
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import get_settings

ALGORITHM = "HS256"

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(subject: str, additional_claims: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)

    payload: dict[str, Any] = {
        "sub": subject,
        "type": "access",
        "iat": now,
        "exp": expires_at,
    }

    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[ALGORITHM],
        )
    except InvalidTokenError:
        return None

    if payload.get("type") != "access":
        return None

    return payload
""")


write_file("backend/app/schemas/user.py", r"""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    user_id: str
    email: EmailStr
    full_name: str | None = None
    anonymous_id: str | None = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    last_seen_at: datetime


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    anonymous_id: str | None = Field(default=None, max_length=120)


class UserProfileResponse(BaseModel):
    profile_id: str
    user_id: str
    anonymous_id: str | None = None
    skin_type: str | None = None
    concerns: list[str] = Field(default_factory=list)
    budget: str | None = None
    excluded_ingredients: list[str] = Field(default_factory=list)
    custom_restrictions: list[str] = Field(default_factory=list)
    experience: str | None = None
    values: list[str] = Field(default_factory=list)
    questionnaire_history: list[dict] = Field(default_factory=list)
    feedback_history: list[dict] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class UserProfileUpdate(BaseModel):
    skin_type: str | None = None
    concerns: list[str] | None = None
    budget: str | None = None
    excluded_ingredients: list[str] | None = None
    custom_restrictions: list[str] | None = None
    experience: str | None = None
    values: list[str] | None = None
""")


write_file("backend/app/schemas/auth.py", r"""
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
""")


write_file("backend/app/repositories/user_repository.py", r"""
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.asynchronous.database import AsyncDatabase

from app.core.time import utc_now


def _clean_user(document: dict[str, Any]) -> dict[str, Any]:
    document["user_id"] = str(document.pop("_id"))
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
            "email": email.lower().strip(),
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

    async def find_raw_by_email(self, email: str) -> dict[str, Any] | None:
        return await self.collection.find_one({"email": email.lower().strip()})

    async def find_raw_by_id(self, user_id: str) -> dict[str, Any] | None:
        try:
            object_id = ObjectId(user_id)
        except InvalidId:
            return None

        return await self.collection.find_one({"_id": object_id})

    async def find_by_id(self, user_id: str) -> dict[str, Any] | None:
        document = await self.find_raw_by_id(user_id)

        if document is None:
            return None

        return _clean_user(document)

    async def touch_last_seen(self, user_id: str) -> None:
        try:
            object_id = ObjectId(user_id)
        except InvalidId:
            return

        await self.collection.update_one(
            {"_id": object_id},
            {
                "$set": {
                    "last_seen_at": utc_now(),
                    "updated_at": utc_now(),
                }
            },
        )

    async def update_user(
        self,
        user_id: str,
        full_name: str | None = None,
        anonymous_id: str | None = None,
    ) -> dict[str, Any] | None:
        try:
            object_id = ObjectId(user_id)
        except InvalidId:
            return None

        update: dict[str, Any] = {"updated_at": utc_now()}

        if full_name is not None:
            update["full_name"] = full_name

        if anonymous_id is not None:
            update["anonymous_id"] = anonymous_id

        await self.collection.update_one(
            {"_id": object_id},
            {"$set": update},
        )

        return await self.find_by_id(user_id)
""")


write_file("backend/app/repositories/profile_repository.py", r"""
from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.core.time import utc_now


def _clean_profile(document: dict[str, Any]) -> dict[str, Any]:
    document["profile_id"] = str(document.pop("_id"))
    return document


class ProfileRepository:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.collection = database["user_profiles"]

    async def create_default_profile(
        self,
        user_id: str,
        anonymous_id: str | None = None,
    ) -> dict[str, Any]:
        now = utc_now()

        document = {
            "user_id": user_id,
            "anonymous_id": anonymous_id,
            "skin_type": None,
            "concerns": [],
            "budget": None,
            "excluded_ingredients": [],
            "custom_restrictions": [],
            "experience": None,
            "values": [],
            "questionnaire_history": [],
            "feedback_history": [],
            "created_at": now,
            "updated_at": now,
        }

        result = await self.collection.insert_one(document)
        document["_id"] = result.inserted_id

        return _clean_profile(document)

    async def find_by_user_id(self, user_id: str) -> dict[str, Any] | None:
        document = await self.collection.find_one({"user_id": user_id})

        if document is None:
            return None

        return _clean_profile(document)

    async def ensure_profile(
        self,
        user_id: str,
        anonymous_id: str | None = None,
    ) -> dict[str, Any]:
        profile = await self.find_by_user_id(user_id)

        if profile is not None:
            return profile

        return await self.create_default_profile(
            user_id=user_id,
            anonymous_id=anonymous_id,
        )

    async def update_profile(
        self,
        user_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        allowed_fields = {
            "skin_type",
            "concerns",
            "budget",
            "excluded_ingredients",
            "custom_restrictions",
            "experience",
            "values",
        }

        update = {
            key: value
            for key, value in payload.items()
            if key in allowed_fields and value is not None
        }

        update["updated_at"] = utc_now()

        await self.collection.update_one(
            {"user_id": user_id},
            {"$set": update},
        )

        return await self.find_by_user_id(user_id)

    async def sync_anonymous_id(
        self,
        user_id: str,
        anonymous_id: str | None,
    ) -> None:
        if anonymous_id is None:
            return

        await self.collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "anonymous_id": anonymous_id,
                    "updated_at": utc_now(),
                }
            },
        )
""")


write_file("backend/app/services/auth_service.py", r"""
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from app.schemas.user import UserProfileResponse, UserResponse


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        profile_repository: ProfileRepository,
    ) -> None:
        self.user_repository = user_repository
        self.profile_repository = profile_repository

    async def register(self, payload: RegisterRequest) -> AuthResponse | None:
        existing = await self.user_repository.find_raw_by_email(payload.email)

        if existing is not None:
            return None

        user = await self.user_repository.create_user(
            email=payload.email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
            anonymous_id=payload.anonymous_id,
        )

        profile = await self.profile_repository.ensure_profile(
            user_id=user["user_id"],
            anonymous_id=user.get("anonymous_id"),
        )

        access_token = create_access_token(
            subject=user["user_id"],
            additional_claims={"email": user["email"]},
        )

        return AuthResponse(
            access_token=access_token,
            user=UserResponse(**user),
            profile=UserProfileResponse(**profile),
        )

    async def login(self, payload: LoginRequest) -> AuthResponse | None:
        raw_user = await self.user_repository.find_raw_by_email(payload.email)

        if raw_user is None:
            return None

        if not raw_user.get("is_active", True):
            return None

        if not verify_password(payload.password, raw_user["password_hash"]):
            return None

        user_id = str(raw_user["_id"])
        await self.user_repository.touch_last_seen(user_id)

        user = await self.user_repository.find_by_id(user_id)

        if user is None:
            return None

        profile = await self.profile_repository.ensure_profile(
            user_id=user["user_id"],
            anonymous_id=user.get("anonymous_id"),
        )

        access_token = create_access_token(
            subject=user["user_id"],
            additional_claims={"email": user["email"]},
        )

        return AuthResponse(
            access_token=access_token,
            user=UserResponse(**user),
            profile=UserProfileResponse(**profile),
        )

    async def get_current_user(self, token: str) -> dict | None:
        payload = decode_access_token(token)

        if payload is None:
            return None

        user_id = payload.get("sub")

        if not user_id:
            return None

        user = await self.user_repository.find_by_id(user_id)

        if user is None:
            return None

        await self.user_repository.touch_last_seen(user_id)
        return user
""")


write_file("backend/app/services/user_service.py", r"""
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserProfileResponse, UserProfileUpdate, UserResponse, UserUpdate


class UserService:
    def __init__(
        self,
        user_repository: UserRepository,
        profile_repository: ProfileRepository,
    ) -> None:
        self.user_repository = user_repository
        self.profile_repository = profile_repository

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

        updated = await self.profile_repository.update_profile(
            user_id=profile["user_id"],
            payload=payload.model_dump(),
        )

        if updated is None:
            return None

        return UserProfileResponse(**updated)
""")


write_file("backend/app/api/v1/dependencies.py", r"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.db.mongodb import get_database
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_auth_service(database=Depends(get_database)) -> AuthService:
    return AuthService(
        user_repository=UserRepository(database),
        profile_repository=ProfileRepository(database),
    )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    user = await service.get_current_user(token)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
""")


write_file("backend/app/api/v1/endpoints/auth.py", r"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.dependencies import get_auth_service
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    result = await service.register(payload)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    return result


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    result = await service.login(payload)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    return result
""")


write_file("backend/app/api/v1/endpoints/users.py", r"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.dependencies import get_current_user
from app.db.mongodb import get_database
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserProfileResponse, UserProfileUpdate, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(database=Depends(get_database)) -> UserService:
    return UserService(
        user_repository=UserRepository(database),
        profile_repository=ProfileRepository(database),
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
""")


write_file("backend/app/api/v1/router.py", r"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    feedback,
    health,
    products,
    questionnaire,
    recommendations,
    replacements,
    restrictions,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(questionnaire.router)
api_router.include_router(restrictions.router)
api_router.include_router(products.router)
api_router.include_router(recommendations.router)
api_router.include_router(feedback.router)
api_router.include_router(replacements.router)
""")


write_file("backend/tests/test_auth_users.py", r"""
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def _unique_email() -> str:
    return f"test-{uuid4().hex}@example.com"


def _register_user(client: TestClient) -> tuple[str, dict]:
    email = _unique_email()

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "Test User",
            "anonymous_id": "auth-test-anon",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    return payload["access_token"], payload


def test_user_can_register() -> None:
    with TestClient(app) as client:
        _, payload = _register_user(client)

    assert payload["token_type"] == "bearer"
    assert payload["user"]["email"]
    assert payload["user"]["full_name"] == "Test User"
    assert payload["user"]["anonymous_id"] == "auth-test-anon"
    assert payload["profile"]["user_id"] == payload["user"]["user_id"]


def test_duplicate_registration_returns_409() -> None:
    email = _unique_email()

    with TestClient(app) as client:
        first = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "StrongPassword123!",
                "full_name": "First User",
                "anonymous_id": "dup-anon",
            },
        )
        second = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "StrongPassword123!",
                "full_name": "Second User",
                "anonymous_id": "dup-anon-2",
            },
        )

    assert first.status_code == 201
    assert second.status_code == 409


def test_user_can_login() -> None:
    email = _unique_email()
    password = "StrongPassword123!"

    with TestClient(app) as client:
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Login User",
                "anonymous_id": "login-anon",
            },
        )
        assert register_response.status_code == 201

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

    assert login_response.status_code == 200
    payload = login_response.json()
    assert payload["access_token"]
    assert payload["user"]["email"] == email


def test_login_with_wrong_password_returns_401() -> None:
    email = _unique_email()

    with TestClient(app) as client:
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "StrongPassword123!",
                "full_name": "Wrong Password User",
                "anonymous_id": "wrong-password-anon",
            },
        )
        assert register_response.status_code == 201

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": "WrongPassword123!",
            },
        )

    assert login_response.status_code == 401


def test_get_me_requires_valid_token() -> None:
    with TestClient(app) as client:
        token, register_payload = _register_user(client)

        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == register_payload["user"]["user_id"]


def test_get_me_without_token_returns_401() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/users/me")

    assert response.status_code == 401


def test_user_can_update_profile() -> None:
    with TestClient(app) as client:
        token, _ = _register_user(client)

        response = client.patch(
            "/api/v1/users/me/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "skin_type": "combination",
                "concerns": ["acne", "sebum"],
                "budget": "balanced",
                "excluded_ingredients": ["fragrance"],
                "custom_restrictions": ["alcohol"],
                "experience": "beginner",
                "values": ["comfort", "price_quality"],
            },
        )

    assert response.status_code == 200
    payload = response.json()

    assert payload["skin_type"] == "combination"
    assert "acne" in payload["concerns"]
    assert payload["budget"] == "balanced"
    assert "fragrance" in payload["excluded_ingredients"]


def test_user_can_update_basic_info() -> None:
    with TestClient(app) as client:
        token, _ = _register_user(client)

        response = client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "full_name": "Updated User",
                "anonymous_id": "updated-anon",
            },
        )

    assert response.status_code == 200
    payload = response.json()

    assert payload["full_name"] == "Updated User"
    assert payload["anonymous_id"] == "updated-anon"
""")


write_file(".gitlab-ci.yml", r"""
stages:
  - test

backend-tests:
  stage: test
  image: python:3.12-slim

  services:
    - name: mongo:7
      alias: mongo
      command: ["--quiet"]

  variables:
    APP_NAME: "KOYASH API"
    APP_ENV: "test"
    API_V1_PREFIX: "/api/v1"

    MONGO_INITDB_ROOT_USERNAME: "koyash"
    MONGO_INITDB_ROOT_PASSWORD: "koyash_dev_password"
    MONGO_INITDB_DATABASE: "koyash_test"

    MONGO_URI: "mongodb://koyash:koyash_dev_password@mongo:27017/?authSource=admin"
    MONGO_DB_NAME: "koyash_test"

    CORS_ORIGINS: "http://localhost:5173,http://127.0.0.1:5173"
    JWT_SECRET_KEY: "test_secret_key"
    ACCESS_TOKEN_EXPIRE_MINUTES: "60"
    ANALYTICS_RAW_EVENT_TTL_DAYS: "30"

    PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"
    PIP_DISABLE_PIP_VERSION_CHECK: "1"

  cache:
    paths:
      - .cache/pip

  before_script:
    - cd backend
    - python --version
    - python -m pip --version
    - python -m pip install --no-cache-dir -r requirements.txt

  script:
    - pytest tests/test_health.py tests/test_questionnaire.py tests/test_restrictions.py tests/test_products.py tests/test_recommendations.py tests/test_feedback_replacements.py tests/test_auth_users.py
""")

print("Step 2.6 auth and user profiles files written successfully.")