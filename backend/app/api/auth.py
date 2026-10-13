
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database.deps import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import authenticate_user, login_user

from app.core.auth import get_current_user
from app.models.user import User
from app.core.auth import require_roles

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db,
        credentials.username,
        credentials.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password, or account inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return login_user(user)


@router.get("/admin-test")
def admin_test(
    current_user: User = Depends(require_roles("ADMIN")),
):
    return {
        "message": "Admin access granted",
        "username": current_user.username,
        "role": current_user.role,
    }


@router.get("/me")
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "is_active": current_user.is_active,
    }
