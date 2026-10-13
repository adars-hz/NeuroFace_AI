
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.database.deps import get_db
from app.models.classroom import Classroom
from app.models.subject import Subject
from app.models.user import User
from app.schemas.subject import SubjectCreate, SubjectResponse
from app.services.subject_service import create_subject

router = APIRouter(prefix="/subjects", tags=["Subjects"])


@router.post(
    "/",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_subject(
    data: SubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    classroom = (
        db.query(Classroom)
        .filter(Classroom.id == data.class_id)
        .first()
    )

    if classroom is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    code = data.subject_code.strip().upper()

    if db.query(Subject).filter(Subject.subject_code == code).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Subject code already exists",
        )

    try:
        return create_subject(db, data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Subject code already exists",
        )


@router.get("/", response_model=list[SubjectResponse])
def list_subjects(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    return db.query(Subject).order_by(Subject.id).all()
