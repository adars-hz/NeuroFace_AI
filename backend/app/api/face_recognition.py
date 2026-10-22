
from datetime import datetime, timezone
from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.database.deps import get_db
from app.models.attendance_record import AttendanceRecord
from app.models.attendance_session import AttendanceSession
from app.models.classroom import Classroom
from app.models.face_embedding import FaceEmbedding
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.teacher_assignment import TeacherAssignment
from app.models.user import User
from app.services.face_matching_service import find_matching_student
from app.services.face_recognition_service import generate_embedding

router = APIRouter(
    prefix="/face-recognition",
    tags=["Face Recognition"],
)

MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def read_face_image(file: UploadFile) -> Image.Image:
    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(status_code=400, detail="Empty image.")

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Image exceeds 5 MB.")

    try:
        image = Image.open(BytesIO(content))
        image_format = image.format
        image.verify()

        if image_format not in ALLOWED_FORMATS:
            raise HTTPException(
                status_code=400,
                detail="Use a JPEG, PNG, or WEBP image.",
            )

        return Image.open(BytesIO(content)).convert("RGB")

    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid image.")


@router.post("/identify")
async def identify_face(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "TEACHER")),
):
    image = await read_face_image(file)

    try:
        embedding = generate_embedding(image)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Face recognition is temporarily unavailable.",
        )

    result = find_matching_student(db, embedding)

    return {
        "matched": result["matched"],
        "student_id": result["student_id"],
        "similarity": result["similarity"],
        "message": result["message"],
    }


@router.post("/mark-attendance")
async def recognize_and_mark_attendance(
    session_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "TEACHER")),
):
    # Validate the attendance session.
    session = (
        db.query(AttendanceSession)
        .filter(AttendanceSession.id == session_id)
        .first()
    )

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    now = utc_now_naive()

    if session.status != "ACTIVE" or session.expires_at <= now:
        if session.status == "ACTIVE" and session.expires_at <= now:
            session.status = "EXPIRED"
            session.ended_at = now
            db.commit()

        raise HTTPException(
            status_code=409,
            detail="This attendance session is not active.",
        )

    # Find the class and subject assignment for this session.
    assignment = (
        db.query(TeacherAssignment)
        .filter(TeacherAssignment.id == session.assignment_id)
        .first()
    )

    if assignment is None:
        raise HTTPException(
            status_code=409,
            detail="The session's teacher assignment was not found.",
        )

    # A teacher may mark attendance only for their own assignment.
    if current_user.role == "TEACHER":
        teacher = (
            db.query(Teacher)
            .filter(Teacher.user_id == current_user.id)
            .first()
        )

        if teacher is None or teacher.id != assignment.teacher_id:
            raise HTTPException(
                status_code=403,
                detail="You cannot mark attendance for this session.",
            )

    # Recognize the face in the uploaded image.
    image = await read_face_image(file)

    try:
        embedding = generate_embedding(image)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Face recognition is temporarily unavailable.",
        )

    result = find_matching_student(db, embedding)

    if not result["matched"] or result["student_id"] is None:
        return {
            "marked": False,
            "student_id": None,
            "similarity": result["similarity"],
            "message": "Unknown or unapproved face. Attendance was not recorded.",
        }

    student = (
        db.query(Student)
        .filter(Student.id == result["student_id"])
        .first()
    )

    if student is None:
        raise HTTPException(
            status_code=409,
            detail="The matched student record was not found.",
        )

    classroom = (
        db.query(Classroom)
        .filter(Classroom.id == assignment.class_id)
        .first()
    )

    if classroom is None:
        raise HTTPException(
            status_code=409,
            detail="The assigned class was not found.",
        )

    if student.class_name.strip().casefold() != classroom.class_name.strip().casefold():
        return {
            "marked": False,
            "student_id": student.id,
            "similarity": result["similarity"],
            "message": "Recognized student belongs to another class.",
        }

    # Prevent duplicate attendance for this student and session.
    existing = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.session_id == session.id,
            AttendanceRecord.student_id == student.id,
        )
        .first()
    )

    if existing:
        return {
            "marked": False,
            "student_id": student.id,
            "student_name": student.full_name,
            "similarity": result["similarity"],
            "message": "Attendance was already recorded for this student.",
        }

    record = AttendanceRecord(
        session_id=session.id,
        student_id=student.id,
        status="PRESENT",
        marked_by=current_user.id,
    )

    db.add(record)

    try:
        db.commit()
        db.refresh(record)
    except IntegrityError:
        db.rollback()
        return {
            "marked": False,
            "student_id": student.id,
            "student_name": student.full_name,
            "similarity": result["similarity"],
            "message": "Attendance was already recorded for this student.",
        }

    return {
        "marked": True,
        "attendance_record_id": record.id,
        "student_id": student.id,
        "student_name": student.full_name,
        "similarity": result["similarity"],
        "message": "Attendance marked successfully.",
    }
