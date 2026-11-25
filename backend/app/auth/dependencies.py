from datetime import UTC, datetime

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import ApiProblem
from app.core.security import hash_token, tokens_equal
from app.db.models import SessionModel, User
from app.db.session import get_db


def find_session(request: Request, db: Session, settings: Settings) -> SessionModel | None:
    raw_token = request.cookies.get(settings.session_cookie_name)
    if not raw_token:
        return None
    session = db.execute(
        select(SessionModel).where(SessionModel.token_hash == hash_token(raw_token))
    ).scalar_one_or_none()
    if session is None:
        return None
    now = datetime.now(UTC)
    if session.revoked_at is not None or session.expires_at <= now:
        return None
    request.state.session = session
    return session


def optional_user(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User | None:
    session = find_session(request, db, settings)
    if session is None:
        return None
    user = db.get(User, session.user_id)
    return user


def current_user(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    user = optional_user(request, db, settings)
    if user is None:
        raise ApiProblem("unauthenticated", 401, "Authentication is required.")
    return user


def current_session(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> SessionModel:
    session = find_session(request, db, settings)
    if session is None:
        raise ApiProblem("unauthenticated", 401, "Authentication is required.")
    return session


def require_csrf(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> None:
    provided = request.headers.get("X-CSRF-Token")
    if not provided:
        raise ApiProblem("csrf_invalid", 403, "A valid CSRF token is required.")
    session = find_session(request, db, settings)
    if session is not None:
        expected_hash = session.csrf_token_hash
    else:
        anonymous_token = request.cookies.get(settings.csrf_cookie_name)
        expected_hash = hash_token(anonymous_token) if anonymous_token else ""
    if not expected_hash or not tokens_equal(hash_token(provided), expected_hash):
        raise ApiProblem("csrf_invalid", 403, "A valid CSRF token is required.")
    db.rollback()


def require_admin(user: User = Depends(current_user)) -> User:
    if user.role != "admin":
        raise ApiProblem("forbidden", 403, "Administrator access is required.")
    return user
