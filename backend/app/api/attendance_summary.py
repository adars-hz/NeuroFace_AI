
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.database.deps import get_db
from app.models.attendance_record import AttendanceRecord
from app.models.attendance_session import AttendanceSession
from app.models.classroom import Classroom
from app.models.face_embedding import FaceEmbedding
from app.models.medical_waiver import MedicalWaiver
from app.models.student import Student
from app.models.subject import Subject
from app.models.teacher_assignment import TeacherAssignment
from app.models.user import User

router = APIRouter(prefix="/attendance-summary", tags=["Attendance Summary"])

MINIMUM_ATTENDANCE = 85.0


@router.get("/my")
def get_my_attendance_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "STUDENT":
        raise HTTPException(
            status_code=403,
            detail="Student access required",
        )

    student = (
        db.query(Student)
        .filter(Student.user_id == current_user.id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student profile not found",
        )

    # Match the student's class to configured classes.
    classrooms = (
        db.query(Classroom)
        .filter(Classroom.class_name.ilike(student.class_name.strip()))
        .all()
    )

    if not classrooms:
        return {
            "student_id": student.id,
            "minimum_attendance": MINIMUM_ATTENDANCE,
            "subjects": [],
        }

    classroom_ids = [classroom.id for classroom in classrooms]

    assignments = (
        db.query(TeacherAssignment, Subject)
        .join(
            Subject,
            Subject.id == TeacherAssignment.subject_id,
        )
        .filter(TeacherAssignment.class_id.in_(classroom_ids))
        .all()
    )

    results = []

    for assignment, subject in assignments:
        # Only closed or expired sessions count toward the calculation.
        sessions = (
            db.query(AttendanceSession)
            .filter(
                AttendanceSession.assignment_id == assignment.id,
                AttendanceSession.status.in_(["CLOSED", "EXPIRED"]),
            )
            .all()
        )

        total_sessions = len(sessions)
        session_ids = [session.id for session in sessions]

        present_count = 0

        if session_ids:
            present_count = (
                db.query(AttendanceRecord)
                .filter(
                    AttendanceRecord.session_id.in_(session_ids),
                    AttendanceRecord.student_id == student.id,
                    AttendanceRecord.status == "PRESENT",
                )
                .count()
            )

        # Approved waiver dates are displayed separately.
        # They do not rewrite attendance records or automatically
        # convert an absence into attendance.
        waivers = (
            db.query(MedicalWaiver)
            .filter(
                MedicalWaiver.student_id == student.id,
                MedicalWaiver.subject_id == subject.id,
                MedicalWaiver.status == "APPROVED",
            )
            .all()
        )

        waiver_dates = []
        for waiver in waivers:
            waiver_dates.append({
                "start_date": waiver.start_date.isoformat(),
                "end_date": waiver.end_date.isoformat(),
            })

        percentage = (
            round((present_count / total_sessions) * 100, 2)
            if total_sessions
            else 0.0
        )

        results.append({
            "subject_id": subject.id,
            "subject_code": subject.subject_code,
            "subject_name": subject.subject_name,
            "total_sessions": total_sessions,
            "present_sessions": present_count,
            "attendance_percentage": percentage,
            "exam_eligible": (
                total_sessions > 0
                and percentage >= MINIMUM_ATTENDANCE
            ),
            "approved_medical_waivers": waiver_dates,
        })

    return {
        "student_id": student.id,
        "minimum_attendance": MINIMUM_ATTENDANCE,
        "subjects": results,
    }
