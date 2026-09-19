from fastapi import APIRouter, Depends
from app.utils.security import get_current_user
from app.models.tasks import User
from app.schemas.users import UserResponse


router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    Returns authenticated user's profile

    - **Auth:** required (`Authorization: Bearer <token>`)
    - **200:** student record for the JWT `sub` (same shape as `StudentResponse`)
    - **401:** missing, invalid, expired token, or user id in the token no longer exists
    """
    return current_user