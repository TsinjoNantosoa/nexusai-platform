from fastapi import APIRouter, Depends

from app.auth.dependencies import current_user
from app.auth.service import user_payload
from app.db.models import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def me(user: User = Depends(current_user)) -> dict[str, object]:
    return user_payload(user)
