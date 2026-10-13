from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pymongo.asynchronous.database import AsyncDatabase

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


def get_auth_service(
    database: Annotated[AsyncDatabase[Any], Depends(get_database)],
) -> AuthService:
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

    try:
        token_auth_version = int(payload.get("auth_version", 0))
        user_auth_version = int(user.get("auth_version", 0))
    except (TypeError, ValueError):
        raise credentials_exception from None

    if token_auth_version != user_auth_version:
        raise credentials_exception

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
