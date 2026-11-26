from fastapi import APIRouter, Depends

from app.auth.dependencies import require_admin
from app.db.models import User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/reports")
def reports(_: User = Depends(require_admin)) -> list[object]:
    return []
