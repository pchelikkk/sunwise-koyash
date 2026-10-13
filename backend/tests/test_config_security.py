import pytest
from pydantic import ValidationError

from app.core.config import Settings


def _settings(*, app_env: str, jwt_secret_key: str) -> Settings:
    return Settings(
        APP_ENV=app_env,
        JWT_SECRET_KEY=jwt_secret_key,
        MONGO_URI="mongodb://example.invalid/koyash",
        _env_file=None,
    )


@pytest.mark.parametrize(
    "secret",
    [
        "change_me",
        "change_me_in_real_environment",
        "koyash_development_only_change_before_prod_2026",
        "short-production-secret",
    ],
)
def test_production_rejects_weak_jwt_secret(secret: str) -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        _settings(app_env="production", jwt_secret_key=secret)


def test_production_accepts_strong_jwt_secret() -> None:
    settings = _settings(
        app_env="production",
        jwt_secret_key="a-unique-production-secret-with-32-bytes-minimum",
    )

    assert settings.is_production is True
