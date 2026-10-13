
from sqlalchemy.orm import Session

from app.core.security import verify_password, create_access_token
from app.models.user import User


def authenticate_user(
    db: Session,
    username: str,
    password: str,
):
    """Verify a user's login credentials."""

    user = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if user is None:
        return None

    if not user.is_active:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def login_user(user: User) -> dict:
    """Generate an access token for an authenticated user."""

    access_token = create_access_token(str(user.id))

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }