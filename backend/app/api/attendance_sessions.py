
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_roles
from app.database.deps import get_db
from app.models.attendance_session import AttendanceSession
from app.models.teacher_assignment import TeacherAssignment
from app.models.teacher import Teacher
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
    # Store UTC timestamps as naive datetimes for MySQL DATETIME.
    return datetime.now(timezone.utc).replace(tzinfo=None)


@router.post(
    "/start",
    response_model=AttendanceSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_session(
    data: AttendanceSessionStart,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("TEACHER")),
):
    teacher = (
        db.query(Teacher)
        .filter(Teacher.user_id == current_user.id)
        .first()
    )

    if teacher is None:
        raise HTTPException(403, "Teacher profile not found")

    assignment = (
        db.query(TeacherAssignment)
        .filter(
            TeacherAssignment.id == data.assignment_id,
            TeacherAssignment.teacher_id == teacher.id,
        )
        .first()
    )

    if assignment is None:
        raise HTTPException(
            403,
            "You are not assigned to this subject and class",
        )

    now = utc_now_naive()

    # Expire any overdue active session for this assignment.
    active_sessions = (
        db.query(AttendanceSession)
        .filter(
            AttendanceSession.assignment_id == assignment.id,
            AttendanceSession.status == "ACTIVE",
        )
        .with_for_update()
        .all()
    )

    for session in active_sessions:
        if session.expires_at <= now:
            session.status = "EXPIRED"
            session.ended_at = session.expires_at
        else:
            raise HTTPException(
                status_code=409,
                detail="An active session already exists for this assignment",
            )

    session = AttendanceSession(
        assignment_id=assignment.id,
        started_at=now,
        expires_at=now + timedelta(minutes=data.duration_minutes),
        status="ACTIVE",
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


@router.post("/{session_id}/close", response_model=AttendanceSessionResponse)
def close_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = (
        db.query(AttendanceSession)
        .filter(AttendanceSession.id == session_id)
        .first()
    )

    if session is None:
        raise HTTPException(404, "Attendance session not found")

    if current_user.role == "TEACHER":
        teacher = (
            db.query(Teacher)
            .filter(Teacher.user_id == current_user.id)
            .first()
        )

        assignment = (
            db.query(TeacherAssignment)
            .filter(
                TeacherAssignment.id == session.assignment_id,
                TeacherAssignment.teacher_id == (
                    teacher.id if teacher else -1
                ),
            )
            .first()
        )

        if assignment is None:
            raise HTTPException(
                403,
                "You cannot close another teacher's session",
            )

    elif current_user.role != "ADMIN":
        raise HTTPException(403, "Permission denied")

    if session.status == "ACTIVE":
        session.status = (
            "EXPIRED"
            if session.expires_at <= utc_now_naive()
            else "CLOSED"
        )
        session.ended_at = utc_now_naive()
        db.commit()
        db.refresh(session)

    return session


@router.get(
    "/",
    response_model=list[AttendanceSessionResponse],
)
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    now = utc_now_naive()

    # Mark overdue sessions as expired when an admin views the list.
    db.query(AttendanceSession).filter(
        AttendanceSession.status == "ACTIVE",
        AttendanceSession.expires_at <= now,
    ).update(
        {
            AttendanceSession.status: "EXPIRED",
            AttendanceSession.ended_at: AttendanceSession.expires_at,
        },
        synchronize_session=False,
    )
    db.commit()

    return (
        db.query(AttendanceSession)
        .order_by(AttendanceSession.id.desc())
        .all()
    )
