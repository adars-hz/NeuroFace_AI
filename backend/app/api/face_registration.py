
from io import BytesIO
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.database.deps import get_db
from app.models.face_registration import FaceRegistration
from app.models.student import Student
from app.models.user import User
from app.schemas.face_registration import FaceRegistrationResponse

router = APIRouter(
    prefix="/face-registration",
    tags=["Face Registration"],
)

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads" / "faces"
MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


@router.post(
    "/",
    response_model=FaceRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_face(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STUDENT")),
):
    student = (
        db.query(Student)
        .filter(Student.user_id == current_user.id)
        .first()
    )

    if student is None:
        raise HTTPException(404, "Student profile not found")

    existing = (
        db.query(FaceRegistration)
        .filter(FaceRegistration.student_id == student.id)
        .first()
    )

    if existing is not None:
        raise HTTPException(
            409,
            "A face registration already exists for this student",
        )

    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(400, "Uploaded file is empty")

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "Image must be 5 MB or smaller")

    try:
        image = Image.open(BytesIO(content))
        image.verify()

        image = Image.open(BytesIO(content))

        if image.format not in ALLOWED_FORMATS:
            raise HTTPException(
                400,
                "Only JPEG, PNG, and WEBP images are accepted",
            )

        if image.width < 100 or image.height < 100:
            raise HTTPException(
                400,
                "Image dimensions must be at least 100 x 100 pixels",
            )

        image = image.convert("RGB")

    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(400, "Uploaded file is not a valid image")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Use a server-generated filename, never the uploaded filename.
    filename = f"student_{student.id}.jpg"
    destination = UPLOAD_DIR / filename
    relative_path = f"uploads/faces/{filename}"

    try:
        image.save(destination, format="JPEG", quality=90)

        registration = FaceRegistration(
            student_id=student.id,
            image_path=relative_path,
            status="PENDING",
        )

        db.add(registration)
        db.commit()
        db.refresh(registration)

        return registration

    except Exception:
        db.rollback()

        if destination.exists():
            destination.unlink()

        raise


@router.get("/my", response_model=FaceRegistrationResponse)
def get_my_face_registration(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STUDENT")),
):
    student = (
        db.query(Student)
        .filter(Student.user_id == current_user.id)
        .first()
    )

    if student is None:
        raise HTTPException(404, "Student profile not found")

    registration = (
        db.query(FaceRegistration)
        .filter(FaceRegistration.student_id == student.id)
        .first()
    )

    if registration is None:
        raise HTTPException(404, "No face registration found")

    return registration
