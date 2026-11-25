import json
import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.admin import router as admin_router
from app.api.health import router as health_router
from app.auth.router import router as auth_router
from app.billing.router import router as billing_router
from app.core.config import Settings, get_settings
from app.core.errors import ApiProblem
from app.db.session import build_engine, build_session_factory
from app.users.router import router as users_router
from app.wallet.router import router as wallet_router

logger = logging.getLogger("nexusai.api")


def error_payload(request: Request, code: str, message: str) -> dict[str, str]:
    return {"code": code, "request_id": request.state.request_id, "message": message}


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    engine = build_engine(settings)
    app.state.engine = engine
    app.state.session_factory = build_session_factory(engine)
    yield
    engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    app = FastAPI(
        title="NexusAI API",
        version="0.1.0",
        description="Phase 2 backend foundation for identity, wallet, and catalogue authority.",
        lifespan=lifespan,
    )
    app.state.settings = resolved
    app.dependency_overrides[get_settings] = lambda: resolved
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=resolved.trusted_hosts + ["testserver"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-CSRF-Token", "Idempotency-Key"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request.state.request_id = request.headers.get("X-Request-ID") or str(uuid4())
        origin = request.headers.get("Origin")
        if (
            request.method not in {"GET", "HEAD", "OPTIONS"}
            and origin
            and origin not in resolved.allowed_origins
        ):
            return JSONResponse(
                status_code=403,
                content=error_payload(request, "origin_forbidden", "Origin is not allowed."),
            )
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("request_failed", extra={"request_id": request.state.request_id})
            raise
        response.headers["X-Request-ID"] = request.state.request_id
        logger.info(
            json.dumps(
                {
                    "request_id": request.state.request_id,
                    "method": request.method,
                    "path": request.url.path,
                }
            )
        )
        return response

    @app.exception_handler(ApiProblem)
    async def api_problem_handler(request: Request, exc: ApiProblem) -> JSONResponse:
        return JSONResponse(
            content=error_payload(request, exc.code, exc.message), status_code=exc.status_code
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            content=error_payload(request, "validation_error", "Request validation failed."),
            status_code=422,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = f"http_{exc.status_code}"
        message = "Request could not be completed."
        if exc.status_code == 404:
            code, message = "not_found", "Resource not found."
        return JSONResponse(
            content=error_payload(request, code, message), status_code=exc.status_code
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled_exception", exc_info=exc, extra={"request_id": request.state.request_id}
        )
        return JSONResponse(
            content=error_payload(request, "internal_error", "Internal server error."),
            status_code=500,
        )

    app.include_router(health_router)
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(wallet_router, prefix="/api/v1")
    app.include_router(billing_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")
    return app


app = create_app()
