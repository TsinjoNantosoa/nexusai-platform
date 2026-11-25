from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.db.session import check_database

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def ready(request: Request) -> JSONResponse:
    try:
        check_database(request.app.state.engine)
    except Exception:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "code": "database_unavailable",
                "request_id": request.state.request_id,
            },
        )
    return JSONResponse(status_code=200, content={"status": "ready"})
