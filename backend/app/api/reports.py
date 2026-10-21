
import csv
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.database.deps import get_db
from app.models.attendance_record import AttendanceRecord
from app.models.attendance_session import AttendanceSession
from app.models.classroom import Classroom
from app.models.leave_request import LeaveRequest
from app.models.medical_waiver import MedicalWaiver
from app.models.student import Student
from app.models.subject import Subject
from app.models.teacher_assignment import TeacherAssignment
from app.models.user import User

router = APIRouter(prefix="/reports", tags=["Reports"])

MINIMUM_ATTENDANCE = 85.0


def require_admin(user: User):
    if user.role != "ADMIN":
        raise HTTPException(403, "Admin access required")


def build_report(db: Session):
    students = db.query(Student).order_by(Student.student_id).all()
    report = []

    for student in students:
        # Match the student's configured class.
        assignments = (
            db.query(TeacherAssignment, Subject)
            .join(
                Subject,
                Subject.id == TeacherAssignment.subject_id,
            )
            .join(
                Classroom,
                Classroom.id == TeacherAssignment.class_id,
            )
            .filter(
                Classroom.class_name.ilike(
                    (student.class_name or "").strip()
                )
            )
            .all()
        )

        for assignment, subject in assignments:
            sessions = (
                db.query(AttendanceSession)
                .filter(
                    AttendanceSession.assignment_id == assignment.id,
                    AttendanceSession.status.in_(["CLOSED", "EXPIRED"]),
                )
                .all()
            )

            session_ids = [s.id for s in sessions]
            total_sessions = len(session_ids)

            records = []
            if session_ids:
                records = (
                    db.query(AttendanceRecord)
                    .filter(
                        AttendanceRecord.session_id.in_(session_ids),
                        AttendanceRecord.student_id == student.id,
                    )
                    .all()
                )

            present = sum(r.status == "PRESENT" for r in records)
            absent = sum(r.status == "ABSENT" for r in records)
            leave_marked = sum(r.status == "LEAVE" for r in records)

            percentage = (
                round(present * 100 / total_sessions, 2)
                if total_sessions
                else 0.0
            )

            leave_requests = (
                db.query(LeaveRequest)
                .filter(
                    LeaveRequest.student_id == student.id,
                    LeaveRequest.subject_id == subject.id,
                )
                .all()
            )

            waivers = (
                db.query(MedicalWaiver)
                .filter(
                    MedicalWaiver.student_id == student.id,
                    MedicalWaiver.subject_id == subject.id,
                    MedicalWaiver.status == "APPROVED",
                )
                .all()
            )

            report.append({
                "student_id": student.student_id,
                "student_name": student.full_name,
                "class_name": student.class_name or "",
                "subject_code": subject.subject_code,
                "subject_name": subject.subject_name,
                "total_sessions": total_sessions,
                "present": present,
                "absent": absent,
                "leave_marked": leave_marked,
                "attendance_percentage": percentage,
                "exam_eligible": (
                    "YES"
                    if total_sessions > 0
                    and percentage >= MINIMUM_ATTENDANCE
                    else "NO"
                ),
                "leave_request_statuses": ", ".join(
                    sorted({item.status for item in leave_requests})
                ),
                "approved_medical_waivers": len(waivers),
            })

    return report


@router.get("/attendance")
def attendance_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    return build_report(db)


@router.get("/attendance.csv")
def download_attendance_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    rows = build_report(db)

    output = StringIO()
    fields = [
        "student_id",
        "student_name",
        "class_name",
        "subject_code",
        "subject_name",
        "total_sessions",
        "present",
        "absent",
        "leave_marked",
        "attendance_percentage",
        "exam_eligible",
        "leave_request_statuses",
        "approved_medical_waivers",
    ]

    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition":
                'attachment; filename="neuroface_attendance_report.csv"'
        },
    )
