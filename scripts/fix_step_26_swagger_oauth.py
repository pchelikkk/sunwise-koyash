from pathlib import Path

ROOT = Path(r"C:\Projects\sunwise-koyash")


def write_file(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip("\n"), encoding="utf-8")


def ensure_requirement(requirement: str) -> None:
    path = ROOT / "backend/requirements.txt"
    lines = path.read_text(encoding="utf-8").splitlines()
    names = [line.split("==")[0].split(">=")[0].strip().lower() for line in lines if line.strip()]
    package_name = requirement.split("==")[0].split(">=")[0].strip().lower()

    if package_name not in names:
        lines.append(requirement)

    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


ensure_requirement("python-multipart>=0.0.12,<1.0")


write_file("backend/app/api/v1/dependencies.py", r"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.db.mongodb import get_database
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


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
from fastapi.security import OAuth2PasswordRequestForm

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


@router.post("/token", response_model=AuthResponse)
async def swagger_oauth_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    result = await service.login(
        LoginRequest(
            email=form_data.username,
            password=form_data.password,
        )
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return result
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


def test_swagger_oauth_token_endpoint_accepts_form_login() -> None:
    email = _unique_email()
    password = "StrongPassword123!"

    with TestClient(app) as client:
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Swagger OAuth User",
                "anonymous_id": "swagger-oauth-anon",
            },
        )
        assert register_response.status_code == 201

        token_response = client.post(
            "/api/v1/auth/token",
            data={
                "username": email,
                "password": password,
            },
        )

    assert token_response.status_code == 200
    payload = token_response.json()
    assert payload["access_token"]
    assert payload["token_type"] == "bearer"
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

print("Step 2.6 Swagger OAuth fix written successfully.")