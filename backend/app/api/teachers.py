
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.database.deps import get_db
from app.models.user import User
from app.models.teacher import Teacher
from app.schemas.teacher import TeacherCreate, TeacherResponse
from app.services.teacher_service import create_teacher

router = APIRouter(prefix="/teachers", tags=["Teachers"])


@router.post(
    "/",
    response_model=TeacherResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_teacher(
    data: TeacherCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(
            status_code=409,
            detail="Username already exists",
        )

    if db.query(Teacher).filter(
        Teacher.employee_id == data.employee_id
    ).first():
        raise HTTPException(
            status_code=409,
            detail="Employee ID already exists",
        )

    try:
        return create_teacher(db, data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Username or employee ID already exists",
        )
