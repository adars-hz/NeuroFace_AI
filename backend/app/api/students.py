
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.database.deps import get_db
from app.models.user import User
from app.models.student import Student
from app.schemas.student import StudentCreate, StudentResponse
from app.services.student_service import create_student

router = APIRouter(prefix="/students", tags=["Students"])


@router.post(
    "/",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_student(
    data: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    username_exists = (
        db.query(User)
        .filter(User.username == data.username)
        .first()
    )

    student_id_exists = (
        db.query(Student)
        .filter(Student.student_id == data.student_id)
        .first()
    )

    if username_exists or student_id_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or student ID already exists",
        )

    try:
        return create_student(db, data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or student ID already exists",
        )
