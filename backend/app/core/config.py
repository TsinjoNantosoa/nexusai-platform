from functools import lru_cache
from typing import Annotated

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NEXUSAI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"
    database_url: str = "postgresql+psycopg://nexusai:nexusai@localhost:55432/nexusai"
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

    @field_validator("allowed_origins", "trusted_hosts", mode="before")
    @classmethod
    def split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        environment = self.environment.lower()
        if self.session_ttl_seconds <= 0:
            raise ValueError("session_ttl_seconds must be positive")
        if self.cookie_samesite.lower() not in {"lax", "strict", "none"}:
            raise ValueError("cookie_samesite must be lax, strict, or none")
        if self.auth_rate_limit <= 0 or self.auth_rate_window_seconds <= 0:
            raise ValueError("Authentication rate-limit settings must be positive")
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
