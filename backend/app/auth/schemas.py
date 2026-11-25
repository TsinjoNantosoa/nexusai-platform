from uuid import UUID

from pydantic import BaseModel, Field, field_validator


def normalize_email(value: str) -> str:
    return value.strip().lower()


class RegisterIn(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)
    age_confirmed: bool
    terms_accepted: bool

    _normalize_email = field_validator("email")(normalize_email)


class LoginIn(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)

    _normalize_email = field_validator("email")(normalize_email)


class UserOut(BaseModel):
    id: UUID
    email: str
    admin: bool


class CsrfOut(BaseModel):
    csrf_token: str
