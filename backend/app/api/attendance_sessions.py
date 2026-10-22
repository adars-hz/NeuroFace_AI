
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.database.deps import get_db
from app.models.attendance_record import AttendanceRecord
from app.models.attendance_session import AttendanceSession
from app.models.classroom import Classroom
from app.models.medical_waiver import MedicalWaiver
from app.models.student import Student
from app.models.subject import Subject
from app.models.teacher_assignment import TeacherAssignment

router = APIRouter(
    prefix="/attendance-summary",
    tags=["Attendance Summary"],
)

MINIMUM_ATTENDANCE = 85.0
FINAL_SESSION_STATUSES = ["CLOSED", "EXPIRED"]


@router.get("/my")
def get_my_attendance_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Only students can view their personal summary.
    if current_user.role != "STUDENT":
        raise HTTPException(
            status_code=403,
            detail="Only students can view their personal attendance summary.",
        )

    student = (
        db.query(Student)
        .filter(Student.user_id == current_user.id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student profile not found.",
        )

    if not student.class_name or not student.class_name.strip():
        return {
            "student_id": student.id,
            "student_name": student.full_name,
            "minimum_attendance": MINIMUM_ATTENDANCE,
            "subjects": [],
            "message": "Your class has not been assigned yet.",
        }

    # Match the student's stored class name to the class table.
    classrooms = (
        db.query(Classroom)
        .filter(
            Classroom.class_name.ilike(student.class_name.strip())
        )
        .all()
    )

    if not classrooms:
        return {
            "student_id": student.id,
            "student_name": student.full_name,
            "minimum_attendance": MINIMUM_ATTENDANCE,
            "subjects": [],
            "message": "No matching classroom was found.",
        }

    classroom_ids = [classroom.id for classroom in classrooms]

    # Collect subjects assigned to the student's class.
    assignments = (
        db.query(TeacherAssignment, Subject)
        .join(
            Subject,
            Subject.id == TeacherAssignment.subject_id,
        )
        .filter(
            TeacherAssignment.class_id.in_(classroom_ids)
        )
        .all()
    )

    # Avoid listing a subject multiple times if multiple teachers
    # have assignments for the same subject and class.
    subject_map = {}

    for assignment, subject in assignments:
        subject_map.setdefault(subject.id, subject)

    results = []

    for subject in subject_map.values():
        subject_assignments = (
            db.query(TeacherAssignment)
            .filter(
                TeacherAssignment.subject_id == subject.id,
                TeacherAssignment.class_id.in_(classroom_ids),
            )
            .all()
        )

        assignment_ids = [
            assignment.id for assignment in subject_assignments
        ]

        sessions = []

        if assignment_ids:
            sessions = (
                db.query(AttendanceSession)
                .filter(
                    AttendanceSession.assignment_id.in_(assignment_ids),
                    AttendanceSession.status.in_(
                        FINAL_SESSION_STATUSES
                    ),
                )
                .all()
            )

        session_ids = [session.id for session in sessions]
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

        present_count = sum(
            1 for record in records
            if record.status == "PRESENT"
        )

        # Missing records are treated as not present in a finalized
        # session. This assumes every finalized session is mandatory
        # for every student enrolled in that class.
        absent_count = max(total_sessions - present_count, 0)

        percentage = (
            round((present_count / total_sessions) * 100, 2)
            if total_sessions > 0
            else 0.0
        )

        eligible = (
            total_sessions > 0
            and percentage >= MINIMUM_ATTENDANCE
        )

        waivers = (
            db.query(MedicalWaiver)
            .filter(
                MedicalWaiver.student_id == student.id,
                MedicalWaiver.subject_id == subject.id,
                MedicalWaiver.status == "APPROVED",
            )
            .order_by(MedicalWaiver.start_date.desc())
            .all()
        )

        approved_waivers = [
            {
                "waiver_id": waiver.id,
                "start_date": waiver.start_date.isoformat(),
                "end_date": waiver.end_date.isoformat(),
                "reason": waiver.reason,
            }
            for waiver in waivers
        ]

        results.append(
            {
                "subject_id": subject.id,
                "subject_code": subject.subject_code,
                "subject_name": subject.subject_name,
                "total_sessions": total_sessions,
                "present_sessions": present_count,
                "absent_sessions": absent_count,
                "attendance_percentage": percentage,
                "minimum_required": MINIMUM_ATTENDANCE,
                "exam_eligible": eligible,
                "eligibility_status": (
                    "ELIGIBLE"
                    if eligible
                    else (
                        "INSUFFICIENT_ATTENDANCE"
                        if total_sessions > 0
                        else "NO_ATTENDANCE_DATA"
                    )
                ),
                "approved_medical_waivers": approved_waivers,
            }
        )

    return {
        "student_id": student.id,
        "student_name": student.full_name,
        "class_name": student.class_name,
        "minimum_attendance": MINIMUM_ATTENDANCE,
        "subjects": results,
    }
