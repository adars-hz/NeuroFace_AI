
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.database.deps import get_db
from app.models.attendance_record import AttendanceRecord
from app.models.attendance_session import AttendanceSession
from app.models.classroom import Classroom
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
    if current_user.role != "STUDENT":
        raise HTTPException(
            status_code=403,
            detail="This endpoint is only for student accounts",
        )

    student = (
        db.query(Student)
        .filter(Student.user_id == current_user.id)
        .first()
    )

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student profile not found",
        )

    assignments = (
        db.query(TeacherAssignment, Subject, Classroom)
        .join(
            Subject,
            Subject.id == TeacherAssignment.subject_id,
        )
        .join(
            Classroom,
            Classroom.id == TeacherAssignment.class_id,
        )
        .filter(
            Classroom.class_name.ilike(student.class_name.strip())
        )
        .all()
    )

    results = []

    for assignment, subject, classroom in assignments:
        # Count only sessions that have finished.
        total_sessions = (
            db.query(AttendanceSession)
            .filter(
                AttendanceSession.assignment_id == assignment.id,
                AttendanceSession.status.in_(["CLOSED", "EXPIRED"]),
            )
            .count()
        )

        # Count this student's PRESENT records for those sessions.
        present_count = (
            db.query(AttendanceRecord)
            .join(
                AttendanceSession,
                AttendanceSession.id == AttendanceRecord.session_id,
            )
            .filter(
                AttendanceRecord.student_id == student.id,
                AttendanceRecord.status == "PRESENT",
                AttendanceSession.assignment_id == assignment.id,
                AttendanceSession.status.in_(["CLOSED", "EXPIRED"]),
            )
            .count()
        )

        percentage = (
            round(present_count / total_sessions * 100, 2)
            if total_sessions > 0
            else 0.0
        )

        results.append({
            "subject_id": subject.id,
            "subject_code": subject.subject_code,
            "subject_name": subject.subject_name,
            "total_sessions": total_sessions,
            "present_sessions": present_count,
            "attendance_percentage": percentage,
            "exam_eligible": percentage >= MINIMUM_ATTENDANCE
            and total_sessions > 0,
        })

    return {
        "student_id": student.student_id,
        "minimum_required_percentage": MINIMUM_ATTENDANCE,
        "subjects": results,
    }
