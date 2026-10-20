
from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.database.deps import get_db
from app.models.leave_request import LeaveRequest
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.user import User

router = APIRouter(prefix="/leave-requests", tags=["Leave Management"])

UPLOAD_DIR = Path("uploads/leave_letters")
MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_TYPES = {"application/pdf", "image/jpeg", "image/png"}


def require_teacher(user: User, db: Session):
    if user.role != "TEACHER":
        raise HTTPException(403, "Teacher access required")

    teacher = db.query(Teacher).filter(
        Teacher.user_id == user.id
    ).first()

    if not teacher:
        raise HTTPException(403, "Teacher profile not found")

    return teacher


@router.post("/upload")
async def upload_leave_letter(
    student_id: int = Form(...),
    subject_id: int = Form(...),
    start_date: date = Form(...),
    end_date: date = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_teacher(current_user, db)

    if start_date > end_date:
        raise HTTPException(400, "Start date must be on or before end date")

    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

    if not student:
        raise HTTPException(404, "Student not found")

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Upload a PDF, JPEG, or PNG file")

    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(400, "The uploaded file is empty")

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "File must be 5 MB or smaller")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    extension = {
        "application/pdf": ".pdf",
        "image/jpeg": ".jpg",
        "image/png": ".png",
    }[file.content_type]

    filename = f"{uuid4().hex}{extension}"
    path = UPLOAD_DIR / filename
    path.write_bytes(content)

    request = LeaveRequest(
        student_id=student_id,
        subject_id=subject_id,
        uploaded_by=current_user.id,
        document_path=str(path),
        start_date=start_date,
        end_date=end_date,
        status="PENDING",
    )

    try:
        db.add(request)
        db.commit()
        db.refresh(request)
    except Exception:
        db.rollback()
        path.unlink(missing_ok=True)
        raise

    return {
        "message": "Leave letter uploaded for review",
        "leave_request_id": request.id,
        "status": request.status,
        "ocr_status": "NOT_PROCESSED",
    }


@router.get("/")
def list_leave_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_teacher(current_user, db)

    requests = (
        db.query(LeaveRequest)
        .order_by(LeaveRequest.created_at.desc())
        .all()
    )

    return [
        {
            "id": item.id,
            "student_id": item.student_id,
            "subject_id": item.subject_id,
            "start_date": item.start_date,
            "end_date": item.end_date,
            "absence_reason": item.absence_reason,
            "status": item.status,
            "review_comment": item.review_comment,
        }
        for item in requests
    ]


@router.patch("/{request_id}/review")
def review_leave_request(
    request_id: int,
    decision: str = Form(...),
    comment: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    teacher = require_teacher(current_user, db)

    decision = decision.strip().upper()

    if decision not in {"APPROVED", "REJECTED"}:
        raise HTTPException(
            400, "Decision must be APPROVED or REJECTED"
        )

    request = db.query(LeaveRequest).filter(
        LeaveRequest.id == request_id
    ).first()

    if not request:
        raise HTTPException(404, "Leave request not found")

    if request.status != "PENDING":
        raise HTTPException(409, "This request has already been reviewed")

    request.status = decision
    request.reviewed_by = current_user.id
    request.reviewed_at = datetime.utcnow()
    request.review_comment = comment.strip() or None

    db.commit()
    db.refresh(request)

    return {
        "message": f"Leave request {decision.lower()}",
        "leave_request_id": request.id,
        "status": request.status,
    }

