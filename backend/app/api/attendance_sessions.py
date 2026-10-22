from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_roles
from app.database.deps import get_db
from app.models.attendance_session import AttendanceSession
from app.models.teacher import Teacher
from app.models.teacher_assignment import TeacherAssignment
from app.models.user import User
from app.schemas.attendance_session import (
    AttendanceSessionStart,
    AttendanceSessionResponse,
)

router = APIRouter(
    prefix="/attendance-sessions",
    tags=["Attendance Sessions"],
)


def utc_now_naive() -> datetime:
    """Return UTC time without timezone information for MySQL DateTime."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_teacher_id(db: Session, user: User) -> int:
    teacher = (
        db.query(Teacher)
        .filter(Teacher.user_id == user.id)
        .first()
    )

    if teacher is None:
        raise HTTPException(
            status_code=404,
            detail="Teacher profile not found",
        )

    return teacher.id


def close_expired_sessions(db: Session) -> None:
    now = utc_now_naive()

    expired_sessions = (
        db.query(AttendanceSession)
        .filter(
            AttendanceSession.status == "ACTIVE",
            AttendanceSession.expires_at <= now,
        )
        .all()
    )

    for session in expired_sessions:
        session.status = "EXPIRED"
        session.ended_at = now

    if expired_sessions:
        db.commit()


@router.post(
    "/",
    response_model=AttendanceSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_attendance_session(
    data: AttendanceSessionStart,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "TEACHER")
    ),
):
    now = utc_now_naive()

    # Clean up expired sessions before checking for conflicts.
    close_expired_sessions(db)

    assignment = (
        db.query(TeacherAssignment)
        .filter(TeacherAssignment.id == data.assignment_id)
        .first()
    )

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail="Teacher assignment not found",
        )

    # Teachers may start sessions only for their own assignments.
    if current_user.role == "TEACHER":
        teacher_id = get_teacher_id(db, current_user)

        if assignment.teacher_id != teacher_id:
            raise HTTPException(
                status_code=403,
                detail="You cannot start a session for this assignment",
            )

    # Prevent concurrent sessions for the same class.
    active_sessions = (
        db.query(AttendanceSession)
        .join(
            TeacherAssignment,
            AttendanceSession.assignment_id == TeacherAssignment.id,
        )
        .filter(
            TeacherAssignment.class_id == assignment.class_id,
            AttendanceSession.status == "ACTIVE",
            AttendanceSession.expires_at > now,
        )
        .all()
    )

    if active_sessions:
        raise HTTPException(
            status_code=409,
            detail=(
                "An active attendance session already exists "
                "for this class. Close it before starting another."
            ),
        )

    session = AttendanceSession(
        assignment_id=assignment.id,
        started_at=now,
        expires_at=now.replace() ,
        status="ACTIVE",
    )

    # Set expiry using the duration selected by the teacher.
    from datetime import timedelta

    session.expires_at = now + timedelta(
        minutes=data.duration_minutes
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


@router.get(
    "/",
    response_model=list[AttendanceSessionResponse],
)
def list_attendance_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("ADMIN", "TEACHER"):
        raise HTTPException(
            status_code=403,
            detail="You cannot view attendance sessions",
        )

    close_expired_sessions(db)

    query = db.query(AttendanceSession)

    if current_user.role == "TEACHER":
        teacher_id = get_teacher_id(db, current_user)

        query = query.join(
            TeacherAssignment,
            AttendanceSession.assignment_id == TeacherAssignment.id,
        ).filter(
            TeacherAssignment.teacher_id == teacher_id
        )

    return query.order_by(
        AttendanceSession.started_at.desc()
    ).all()


@router.patch(
    "/{session_id}/close",
    response_model=AttendanceSessionResponse,
)
def close_attendance_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "TEACHER")
    ),
):
    session = (
        db.query(AttendanceSession)
        .filter(AttendanceSession.id == session_id)
        .first()
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Attendance session not found",
        )

    if current_user.role == "TEACHER":
        teacher_id = get_teacher_id(db, current_user)

        assignment = (
            db.query(TeacherAssignment)
            .filter(
                TeacherAssignment.id == session.assignment_id
            )
            .first()
        )

        if assignment is None or assignment.teacher_id != teacher_id:
            raise HTTPException(
                status_code=403,
                detail="You cannot close this attendance session",
            )

    now = utc_now_naive()

    if session.status == "ACTIVE" and session.expires_at <= now:
        session.status = "EXPIRED"
        session.ended_at = now
    elif session.status == "ACTIVE":
        session.status = "CLOSED"
        session.ended_at = now

    db.commit()
    db.refresh(session)

    return session
