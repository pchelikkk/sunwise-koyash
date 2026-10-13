from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
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

    import_dataset_on_startup: bool = Field(default=True, alias="IMPORT_DATASET_ON_STARTUP")
    product_dataset_path: str = Field(
        default="/data/products.xlsx",
        alias="PRODUCT_DATASET_PATH",
    )

    # Optional explanation providers. Product choice and safety remain deterministic.
    # Important: the recommendation engine does NOT use LLM to choose products.
    # LLM can only rewrite already computed explanations in KOYASH tone.
    llm_enabled: bool = Field(default=False, alias="LLM_ENABLED")
    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    llm_timeout_seconds: float = Field(default=12.0, alias="LLM_TIMEOUT_SECONDS")

    vsellm_api_key: str | None = Field(default=None, alias="VSELLM_API_KEY")
    vsellm_base_url: str = Field(default="https://api.vsellm.ru/v1", alias="VSELLM_BASE_URL")
    vsellm_model: str = Field(default="openai/gpt-4o-mini", alias="VSELLM_MODEL")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        alias="OPENAI_BASE_URL",
    )
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

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

    @property
    def product_dataset_file(self) -> Path:
        return Path(self.product_dataset_path)

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        secret = self.jwt_secret_key.strip()
        insecure_placeholders = {
            "change_me",
            "change_me_in_real_environment",
            "koyash_development_only_change_before_prod_2026",
        }

        if self.is_production and (
            secret.lower() in insecure_placeholders
            or len(secret.encode("utf-8")) < 32
        ):
            raise ValueError(
                "JWT_SECRET_KEY must be a non-placeholder secret of at least "
                "32 bytes in production"
            )

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
