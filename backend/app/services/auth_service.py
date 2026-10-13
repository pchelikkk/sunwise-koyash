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
from app.repositories.recommendation_repository import RecommendationRepository
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
        recommendation_repository: RecommendationRepository | None = None,
    ) -> None:
        self.user_repository = user_repository
        self.profile_repository = profile_repository
        self.password_reset_repository = password_reset_repository
        self.email_service = email_service
        self.event_tracking_service = event_tracking_service
        self.recommendation_repository = recommendation_repository

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
        claimed_recommendations = await self._claim_recommendations(
            anonymous_id=payload.anonymous_id,
            user_id=user["user_id"],
        )

        if self.event_tracking_service is not None:
            await self.event_tracking_service.record(
                AnalyticsEventType.REGISTRATION_COMPLETED,
                user_id=user["user_id"],
                anonymous_id=user.get("anonymous_id"),
                metadata={
                    "name_provided": bool(payload.full_name),
                    "pre_registration_session_linked": bool(payload.anonymous_id),
                    "claimed_recommendation_count": claimed_recommendations,
                },
            )

        return self._build_auth_response(
            user=user,
            profile=profile,
            claimed_recommendations=claimed_recommendations,
        )

    async def login(
        self,
        email: str,
        password: str,
        anonymous_id: str | None = None,
    ) -> AuthResponse:
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
        claimed_recommendations = await self._claim_recommendations(
            anonymous_id=anonymous_id,
            user_id=user["user_id"],
        )

        return self._build_auth_response(
            user=user,
            profile=profile,
            claimed_recommendations=claimed_recommendations,
        )

    async def _claim_recommendations(
        self,
        *,
        anonymous_id: str | None,
        user_id: str,
    ) -> int:
        if self.recommendation_repository is None:
            return 0
        return await self.recommendation_repository.claim_anonymous_sessions(
            anonymous_id=anonymous_id,
            user_id=user_id,
        )

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
        reset_token = await self.password_reset_repository.consume_valid_by_hash(
            token_hash
        )

        if reset_token is None:
            raise InvalidResetTokenError

        new_password_hash = create_password_hash(new_password)

        updated = await self.user_repository.update_password(
            user_id=reset_token["user_id"],
            password_hash=new_password_hash,
        )

        if not updated:
            raise InvalidResetTokenError

        await self.password_reset_repository.invalidate_user_tokens(reset_token["user_id"])

        return ResetPasswordResponse(message="Пароль успешно обновлён.")

    def _build_auth_response(
        self,
        user: dict,
        profile: dict,
        claimed_recommendations: int = 0,
    ) -> AuthResponse:
        return AuthResponse(
            access_token=create_access_token(
                user["user_id"],
                auth_version=int(user.get("auth_version", 0)),
            ),
            token_type="bearer",
            user=UserResponse(**user),
            profile=UserProfileResponse(**profile),
            claimed_recommendations=claimed_recommendations,
        )

    def _build_reset_url(self, token: str) -> str:
        settings = get_settings()
        base_url = settings.frontend_base_url.rstrip("/")
        query = urlencode({"token": token})

        return f"{base_url}/#reset?{query}"
