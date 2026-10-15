
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.database.deps import get_db
from app.models.attendance_record import AttendanceRecord
from app.models.attendance_session import AttendanceSession
from app.models.student import Student
from app.models.teacher_assignment import TeacherAssignment
from app.models.subject import Subject
from app.models.user import User

router = APIRouter(
    prefix="/attendance-summary",
    tags=["Attendance Summary"],
)

MINIMUM_ATTENDANCE = 85.0


@router.get("/my")
def my_attendance_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student = (
        db.query(Student)
        .filter(Student.user_id == current_user.id)
        .first()
    )

    if current_user.role != "STUDENT" or student is None:
        raise HTTPException(
            status_code=403,
            detail="This endpoint is only for student accounts",
        )

    assignments = (
        db.query(TeacherAssignment, Subject)
        .join(Subject, Subject.id == TeacherAssignment.subject_id)
        .filter(TeacherAssignment.class_id.isnot(None))
        .all()
    )

    # Use the student's current class name to select relevant subjects.
    from app.models.classroom import Classroom

    classroom = (
        db.query(Classroom)
        .filter(Classroom.id == assignments[0][0].class_id)
        .first()
        if assignments else None
    )

    results = []

    for assignment, subject in assignments:
        classroom = (
            db.query(Classroom)
            .filter(Classroom.id == assignment.class_id)
            .first()
        )

        if (
            classroom is None
            or classroom.class_name.strip().casefold()
            != student.class_name.strip().casefold()
        ):
            continue

        sessions = (
            db.query(AttendanceSession)
            .filter(
                AttendanceSession.assignment_id == assignment.id,
                AttendanceSession.status.in_(["CLOSED", "EXPIRED"]),
            )
            .all()
        )

        total_sessions = len(sessions)
        present_count = (
            db.query(AttendanceRecord)
            .filter(
                AttendanceRecord.student_id == student.id,
                AttendanceRecord.session_id.in_(
                    [s.id for s in sessions]
                ),
                AttendanceRecord.status == "PRESENT",
            )
            .count()
        )

        percentage = (
            round(present_count / total_sessions * 100, 2)
            if total_sessions else 0.0
        )

        results.append({
            "subject_id": subject.id,
            "subject_code": subject.subject_code,
            "subject_name": subject.subject_name,
            "total_sessions": total_sessions,
            "present_sessions": present_count,
            "attendance_percentage": percentage,
            "exam_eligible": percentage >= MINIMUM_ATTENDANCE,
        })

    return {
        "student_id": student.student_id,
        "minimum_required_percentage": MINIMUM_ATTENDANCE,
        "subjects": results,
    }
