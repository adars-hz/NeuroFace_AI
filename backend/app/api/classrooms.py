
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.database.deps import get_db
from app.models.department import Department
from app.models.classroom import Classroom
from app.models.user import User
from app.schemas.classroom import ClassroomCreate, ClassroomResponse
from app.services.classroom_service import create_classroom

router = APIRouter(prefix="/classrooms", tags=["Classrooms"])


@router.post(
    "/",
    response_model=ClassroomResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_classroom(
    data: ClassroomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    department = (
        db.query(Department)
        .filter(Department.id == data.department_id)
        .first()
    )

    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found",
        )

    existing = (
        db.query(Classroom)
        .filter(Classroom.class_name == data.class_name)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Class name already exists",
        )

    return create_classroom(db, data)


@router.get("/", response_model=list[ClassroomResponse])
def list_classrooms(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    return db.query(Classroom).order_by(Classroom.id).all()

