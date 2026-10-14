
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_roles
from app.database.deps import get_db
from app.models.attendance_record import AttendanceRecord
from app.models.attendance_session import AttendanceSession
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.teacher_assignment import TeacherAssignment
from app.models.classroom import Classroom
from app.models.user import User
from app.schemas.attendance_record import (
    AttendanceRecordCreate,
    AttendanceRecordResponse,
)

router = APIRouter(prefix="/attendance-records", tags=["Attendance Records"])


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@router.post(
    "/",
    response_model=AttendanceRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
def mark_attendance(
    data: AttendanceRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "TEACHER")),
):
    session = (
        db.query(AttendanceSession)
        .filter(AttendanceSession.id == data.session_id)
        .first()
    )

    if session is None:
        raise HTTPException(404, "Attendance session not found")

    now = utc_now_naive()

    if session.status != "ACTIVE" or session.expires_at <= now:
        if session.status == "ACTIVE" and session.expires_at <= now:
            session.status = "EXPIRED"
            session.ended_at = now
            db.commit()

        raise HTTPException(409, "Attendance session is not active")

    assignment = (
        db.query(TeacherAssignment)
        .filter(TeacherAssignment.id == session.assignment_id)
        .first()
    )

    if assignment is None:
        raise HTTPException(409, "Session assignment not found")

    if current_user.role == "TEACHER":
        teacher = (
            db.query(Teacher)
            .filter(Teacher.user_id == current_user.id)
            .first()
        )

        if teacher is None or teacher.id != assignment.teacher_id:
            raise HTTPException(403, "You cannot mark attendance for this session")

    student = (
        db.query(Student)
        .filter(Student.id == data.student_id)
        .first()
    )

    if student is None:
        raise HTTPException(404, "Student not found")

    classroom = (
        db.query(Classroom)
        .filter(Classroom.id == assignment.class_id)
        .first()
    )

    if classroom is None:
        raise HTTPException(409, "Assigned class not found")

    # The current Student model uses class_name rather than class_id.
    if student.class_name.strip().casefold() != classroom.class_name.strip().casefold():
        raise HTTPException(400, "Student does not belong to this session's class")

    record = AttendanceRecord(
        session_id=session.id,
        student_id=student.id,
        status=data.status,
        marked_by=current_user.id,
    )

    db.add(record)

    try:
        db.commit()
        db.refresh(record)
        return record
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Attendance has already been recorded for this student in this session",
        )


@router.get("/", response_model=list[AttendanceRecordResponse])
def list_attendance(
    session_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(AttendanceRecord)

    if current_user.role == "STUDENT":
        student = (
            db.query(Student)
            .filter(Student.user_id == current_user.id)
            .first()
        )

        if student is None:
            raise HTTPException(404, "Student profile not found")

        query = query.filter(AttendanceRecord.student_id == student.id)

    elif current_user.role == "TEACHER":
        teacher = (
            db.query(Teacher)
            .filter(Teacher.user_id == current_user.id)
            .first()
        )

        if teacher is None:
            raise HTTPException(403, "Teacher profile not found")

        assigned_session_ids = (
            db.query(AttendanceSession.id)
            .join(
                TeacherAssignment,
                AttendanceSession.assignment_id == TeacherAssignment.id,
            )
            .filter(TeacherAssignment.teacher_id == teacher.id)
            .subquery()
        )

        query = query.filter(
            AttendanceRecord.session_id.in_(assigned_session_ids)
        )

    if session_id is not None:
        query = query.filter(AttendanceRecord.session_id == session_id)

    return query.order_by(AttendanceRecord.id.desc()).all()
