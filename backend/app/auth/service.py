from datetime import UTC, datetime, timedelta

from fastapi import Response
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import hash_token, new_token
from app.db.models import SessionModel, User


def user_payload(user: User) -> dict[str, object]:
    return {"id": user.id, "email": user.email, "admin": user.role == "admin"}


def issue_session(
    db: Session,
    response: Response,
    user: User,
    settings: Settings,
    previous_session: SessionModel | None = None,
) -> str:
    if previous_session is not None:
        previous_session.revoked_at = datetime.now(UTC)
    raw_session = new_token()
    csrf_token = new_token()
    session = SessionModel(
        user_id=user.id,
        token_hash=hash_token(raw_session),
        csrf_token_hash=hash_token(csrf_token),
        expires_at=datetime.now(UTC) + timedelta(seconds=settings.session_ttl_seconds),
    )
    db.add(session)
    db.commit()
    set_auth_cookies(response, settings, raw_session, csrf_token)
    response.headers["X-CSRF-Token"] = csrf_token
    return csrf_token


def set_auth_cookies(
    response: Response, settings: Settings, session_token: str, csrf_token: str
) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        session_token,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )
    response.set_cookie(
        settings.csrf_cookie_name,
        csrf_token,
        max_age=settings.session_ttl_seconds,
        httponly=False,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )


def revoke_session(db: Session, session: SessionModel) -> None:
    session.revoked_at = datetime.now(UTC)
    db.commit()
