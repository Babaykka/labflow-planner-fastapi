from fastapi import APIRouter

from app.core.deps import CurrentUser
from app.models import User
from app.schemas import UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: CurrentUser) -> User:
    return current_user
