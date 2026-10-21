
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.database.deps import get_db
from app.models.medical_waiver import MedicalWaiver
from app.models.student import Student
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.models.user import User

router = APIRouter(
    prefix="/medical-waivers",
    tags=["Medical Waivers"],
)

UPLOAD_DIR = Path("uploads/medical_certificates")
MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}


def require_hod(user: User, db: Session) -> Teacher:
    if user.role != "TEACHER":
        raise HTTPException(403, "HOD teacher access required")

    teacher = (
        db.query(Teacher)
        .filter(Teacher.user_id == user.id)
        .first()
    )

    if not teacher or (teacher.designation or "").upper() != "HOD":
        raise HTTPException(
            403,
            "Only a teacher designated as HOD can manage medical waivers",
        )

    return teacher


@router.post("/upload")
async def upload_medical_certificate(
    student_id: int = Form(...),
    subject_id: int = Form(...),
    start_date: date = Form(...),
    end_date: date = Form(...),
    reason: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_hod(current_user, db)

    if start_date > end_date:
        raise HTTPException(400, "Start date must not be after end date")

    if not db.query(Student).filter(Student.id == student_id).first():
        raise HTTPException(404, "Student not found")

    if not db.query(Subject).filter(Subject.id == subject_id).first():
        raise HTTPException(404, "Subject not found")

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Upload a PDF, JPEG, or PNG certificate")

    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(400, "Uploaded certificate is empty")

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "Certificate must be 5 MB or smaller")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path = UPLOAD_DIR / f"{uuid4().hex}{ALLOWED_TYPES[file.content_type]}"
    path.write_bytes(content)

    waiver = MedicalWaiver(
        student_id=student_id,
        subject_id=subject_id,
        approved_by=current_user.id,
        start_date=start_date,
        end_date=end_date,
        certificate_path=str(path),
        reason=reason.strip() or None,
        status="PENDING",
    )

    try:
        db.add(waiver)
        db.commit()
        db.refresh(waiver)
    except Exception:
        db.rollback()
        path.unlink(missing_ok=True)
        raise

    return {
        "message": "Medical certificate submitted for review",
        "waiver_id": waiver.id,
        "status": waiver.status,
    }


@router.get("/")
def list_medical_waivers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_hod(current_user, db)

    waivers = (
        db.query(MedicalWaiver)
        .order_by(MedicalWaiver.created_at.desc())
        .all()
    )

    return [
        {
            "id": item.id,
            "student_id": item.student_id,
            "subject_id": item.subject_id,
            "start_date": item.start_date,
            "end_date": item.end_date,
            "reason": item.reason,
            "status": item.status,
            "review_comment": item.review_comment,
        }
        for item in waivers
    ]


@router.patch("/{waiver_id}/review")
def review_medical_waiver(
    waiver_id: int,
    decision: str = Form(...),
    comment: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_hod(current_user, db)

    decision = decision.strip().upper()

    if decision not in {"APPROVED", "REJECTED"}:
        raise HTTPException(
            400,
            "Decision must be APPROVED or REJECTED",
        )

    waiver = (
        db.query(MedicalWaiver)
        .filter(MedicalWaiver.id == waiver_id)
        .first()
    )

    if not waiver:
        raise HTTPException(404, "Medical waiver not found")

    if waiver.status != "PENDING":
        raise HTTPException(409, "This waiver has already been reviewed")

    waiver.status = decision
    waiver.reviewed_at = datetime.now(timezone.utc)
    waiver.review_comment = comment.strip() or None

    db.commit()
    db.refresh(waiver)

    return {
        "message": f"Medical waiver {decision.lower()}",
        "waiver_id": waiver.id,
        "status": waiver.status,
    }
