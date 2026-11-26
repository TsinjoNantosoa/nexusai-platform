import re
from functools import lru_cache
from typing import Annotated
from urllib.parse import urlparse

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NEXUSAI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"
    database_url: str = "postgresql+psycopg://nexusai:nexusai@localhost:56432/nexusai"
    allowed_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    trusted_hosts: Annotated[list[str], NoDecode] = ["localhost", "127.0.0.1"]
    session_cookie_name: str = "nexusai_session"
    csrf_cookie_name: str = "nexusai_csrf"
    session_ttl_seconds: int = 8 * 60 * 60
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    auth_rate_limit: int = 10
    auth_rate_window_seconds: int = 60
    checkout_rate_limit: int = 6
    checkout_rate_window_seconds: int = 60
    stripe_enabled: bool = False
    stripe_secret_key: SecretStr | None = None
    stripe_webhook_secret: SecretStr | None = None
    stripe_api_version: str = "2026-11-18.endive"
    stripe_request_timeout_seconds: int = 30
    stripe_max_network_retries: int = 2
    frontend_base_url: str = "http://localhost:5173"

    @field_validator("allowed_origins", "trusted_hosts", mode="before")
    @classmethod
    def split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("stripe_api_version")
    @classmethod
    def validate_stripe_api_version(cls, value: str) -> str:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:\.[a-z0-9]+)?", value):
            raise ValueError("stripe_api_version must be a Stripe date-based API version")
        return value

    @field_validator("frontend_base_url")
    @classmethod
    def validate_frontend_base_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("frontend_base_url must be an absolute HTTP(S) URL")
        return value.rstrip("/")

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        environment = self.environment.lower()
        if self.session_ttl_seconds <= 0:
            raise ValueError("session_ttl_seconds must be positive")
        if self.cookie_samesite.lower() not in {"lax", "strict", "none"}:
            raise ValueError("cookie_samesite must be lax, strict, or none")
        if self.auth_rate_limit <= 0 or self.auth_rate_window_seconds <= 0:
            raise ValueError("Authentication rate-limit settings must be positive")
        if self.checkout_rate_limit <= 0 or self.checkout_rate_window_seconds <= 0:
            raise ValueError("Checkout rate-limit settings must be positive")
        if self.stripe_request_timeout_seconds <= 0:
            raise ValueError("stripe_request_timeout_seconds must be positive")
        if not 0 <= self.stripe_max_network_retries <= 3:
            raise ValueError("stripe_max_network_retries must be between 0 and 3")
        if self.stripe_secret_key is not None:
            key = self.stripe_secret_key.get_secret_value()
            allowed_prefixes = ("sk_test_", "rk_test_", "rkcs_test_", "csk_rk_test_")
            if not key.startswith(allowed_prefixes):
                raise ValueError("Only Stripe Sandbox API key formats are accepted")
        if self.stripe_enabled and (
            self.stripe_secret_key is None or self.stripe_webhook_secret is None
        ):
            raise ValueError(
                "Stripe requires both Sandbox API and webhook secrets when enabled"
            )
        if self.stripe_enabled and environment in {"production", "prod"}:
            raise ValueError("Stripe Sandbox mode cannot be enabled in production")
        if environment in {"production", "prod"}:
            if not self.cookie_secure:
                raise ValueError("Secure cookies are required in production")
            if not self.allowed_origins or "*" in self.allowed_origins:
                raise ValueError("Production allowed_origins must be explicit")
            if any(not origin.lower().startswith("https://") for origin in self.allowed_origins):
                raise ValueError("Production allowed_origins must use HTTPS")
            if not self.trusted_hosts or "*" in self.trusted_hosts:
                raise ValueError("Production trusted_hosts must be explicit")
            if self.cookie_samesite.lower() == "none" and not self.cookie_secure:
                raise ValueError("SameSite=None requires Secure cookies")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
