
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.database.deps import get_db
from app.models.teacher import Teacher
from app.models.subject import Subject
from app.models.classroom import Classroom
from app.models.teacher_assignment import TeacherAssignment
from app.models.user import User
from app.schemas.teacher_assignment import (
    TeacherAssignmentCreate,
    TeacherAssignmentResponse,
)
from app.services.teacher_assignment_service import create_assignment

router = APIRouter(
    prefix="/teacher-assignments",
    tags=["Teacher Assignments"],
)


@router.post(
    "/",
    response_model=TeacherAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_assignment(
    data: TeacherAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    teacher = db.query(Teacher).filter(
        Teacher.id == data.teacher_id
    ).first()

    if teacher is None:
        raise HTTPException(404, "Teacher not found")

    subject = db.query(Subject).filter(
        Subject.id == data.subject_id
    ).first()

    if subject is None:
        raise HTTPException(404, "Subject not found")

    classroom = db.query(Classroom).filter(
        Classroom.id == data.class_id
    ).first()

    if classroom is None:
        raise HTTPException(404, "Class not found")

    if subject.class_id != data.class_id:
        raise HTTPException(
            status_code=400,
            detail="The subject does not belong to the selected class",
        )

    existing = db.query(TeacherAssignment).filter(
        TeacherAssignment.teacher_id == data.teacher_id,
        TeacherAssignment.subject_id == data.subject_id,
        TeacherAssignment.class_id == data.class_id,
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="This teacher is already assigned to this subject and class",
        )

    try:
        return create_assignment(db, data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Assignment conflicts with an existing record",
        )


@router.get(
    "/",
    response_model=list[TeacherAssignmentResponse],
)
def list_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    return (
        db.query(TeacherAssignment)
        .order_by(TeacherAssignment.id)
        .all()
    )
