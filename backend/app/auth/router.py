from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import ApiProblem
from app.core.rate_limit import SlidingWindowLimiter
from app.core.security import hash_password, hash_token, new_token, verify_password
from app.db.models import SessionModel, User
from app.db.session import get_db
from app.wallet.service import create_initial_wallet

from .dependencies import current_session, find_session, require_csrf
from .schemas import CsrfOut, LoginIn, RegisterIn, UserOut
from .service import issue_session, revoke_session, user_payload

router = APIRouter(prefix="/auth", tags=["auth"])
_limiters: dict[tuple[int, int], SlidingWindowLimiter] = {}


def limiter_for(settings: Settings) -> SlidingWindowLimiter:
    key = (settings.auth_rate_limit, settings.auth_rate_window_seconds)
    limiter = _limiters.get(key)
    if limiter is None:
        limiter = SlidingWindowLimiter(*key)
        _limiters[key] = limiter
    return limiter


def request_key(request: Request, email: str = "") -> str:
    host = request.client.host if request.client else "unknown"
    return f"{host}:{email}"


@router.get("/csrf", response_model=CsrfOut)
def csrf_bootstrap(
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    session = find_session(request, db, settings)
    token = new_token()
    if session is not None:
        session.csrf_token_hash = hash_token(token)
        db.commit()
    response.set_cookie(
        settings.csrf_cookie_name,
        token,
        max_age=settings.session_ttl_seconds,
        httponly=False,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )
    response.headers["X-CSRF-Token"] = token
    return {"csrf_token": token}


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterIn,
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_csrf),
) -> dict[str, object]:
    if not limiter_for(settings).allow(request_key(request, payload.email)):
        raise ApiProblem("rate_limited", 429, "Too many authentication attempts.")
    if not payload.age_confirmed or not payload.terms_accepted:
        raise ApiProblem(
            "registration_requirements", 422, "Registration requirements were not accepted."
        )
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="user",
        age_confirmed=payload.age_confirmed,
        terms_accepted=payload.terms_accepted,
    )
    try:
        db.add(user)
        db.flush()
        create_initial_wallet(db, user)
        db.commit()
    except IntegrityError as error:
        db.rollback()
        if "users_email" in str(error).lower() or "unique" in str(error).lower():
            raise ApiProblem(
                "email_already_registered", 409, "The email or password is not accepted."
            ) from error
        raise
    issue_session(db, response, user, settings)
    return user_payload(user)


@router.post("/login", response_model=UserOut)
def login(
    payload: LoginIn,
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_csrf),
) -> dict[str, object]:
    if not limiter_for(settings).allow(request_key(request, payload.email)):
        raise ApiProblem("rate_limited", 429, "Too many authentication attempts.")
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        db.rollback()
        raise ApiProblem("invalid_credentials", 401, "The email or password is not accepted.")
    previous = find_session(request, db, settings)
    db.rollback()
    issue_session(db, response, user, settings, previous)
    return user_payload(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    session: SessionModel = Depends(current_session),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_csrf),
) -> Response:
    revoke_session(db, session)
    response.delete_cookie(settings.session_cookie_name, path="/")
    response.delete_cookie(settings.csrf_cookie_name, path="/")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
