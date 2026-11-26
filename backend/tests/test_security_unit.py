import pytest
from app.core.config import Settings
from app.core.security import hash_password, hash_token, new_token, tokens_equal, verify_password
from pydantic import ValidationError


def test_argon2_passwords_are_one_way_and_verifiable() -> None:
    password_hash = hash_password("fictional-password-123")
    assert password_hash.startswith("$argon2id$")
    assert password_hash != "fictional-password-123"
    assert verify_password("fictional-password-123", password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_session_tokens_are_random_and_hashed() -> None:
    token = new_token()
    assert len(token) >= 40
    assert hash_token(token) != token
    assert tokens_equal(hash_token(token), hash_token(token))
    assert not tokens_equal(hash_token(token), hash_token(new_token()))


def test_development_configuration_allows_local_http() -> None:
    settings = Settings(
        environment="development",
        allowed_origins=["http://localhost:5173"],
        trusted_hosts=["localhost"],
        cookie_secure=False,
    )

    assert settings.cookie_secure is False


def test_production_configuration_requires_secure_explicit_origins() -> None:
    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            allowed_origins=["https://app.example.test"],
            trusted_hosts=["app.example.test"],
            cookie_secure=False,
        )
    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            allowed_origins=["*"],
            trusted_hosts=["app.example.test"],
            cookie_secure=True,
        )
    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            allowed_origins=["http://app.example.test"],
            trusted_hosts=["app.example.test"],
            cookie_secure=True,
        )
    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            allowed_origins=["https://app.example.test"],
            trusted_hosts=["*"],
            cookie_secure=True,
        )
    with pytest.raises(ValidationError):
        Settings(cookie_samesite="invalid")
    with pytest.raises(ValidationError):
        Settings(session_ttl_seconds=0)

    settings = Settings(
        environment="production",
        allowed_origins=["https://app.example.test"],
        trusted_hosts=["app.example.test"],
        cookie_secure=True,
    )
    assert settings.cookie_secure is True
