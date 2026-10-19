from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from facenet_pytorch import MTCNN
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.database.deps import get_db
from app.models.face_registration import FaceRegistration
from app.models.student import Student
from app.schemas.face_registration import FaceRegistrationResponse
from app.services.face_embedding_service import save_student_embedding

router = APIRouter(
    prefix="/face-registration",
    tags=["Face Registration"],
)

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads" / "faces"
MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}

# Initialize the face detector once when the API module loads.
face_detector = MTCNN(
    keep_all=True,
    device="cpu",
)


@router.post("/", response_model=FaceRegistrationResponse, status_code=201)
async def register_face(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("STUDENT")),
):
    student = (
        db.query(Student)
        .filter(Student.user_id == current_user.id)
        .first()
    )

    if student is None:
        raise HTTPException(status_code=404, detail="Student profile not found")

    existing = (
        db.query(FaceRegistration)
        .filter(FaceRegistration.student_id == student.id)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Face registration already exists for this student",
        )

    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Image must be 5 MB or smaller",
        )

    try:
        image = Image.open(BytesIO(content))
        image_format = image.format
        image.verify()

        image = Image.open(BytesIO(content))

        if image_format not in ALLOWED_FORMATS:
            raise HTTPException(
                status_code=400,
                detail="Only JPEG, PNG, and WEBP images are allowed",
            )

        if image.width < 100 or image.height < 100:
            raise HTTPException(
                status_code=400,
                detail="Image dimensions must be at least 100 x 100 pixels",
            )

        image = image.convert("RGB")

    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        boxes, scores = face_detector.detect(image)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Face detection is temporarily unavailable",
        )

    if boxes is None or scores is None:
        raise HTTPException(
            status_code=400,
            detail="No face detected. Upload a clear photo showing one face.",
        )

    # Ignore detections with low confidence.
    valid_faces = [
        (box, score)
        for box, score in zip(boxes, scores)
        if score is not None and score >= 0.90
    ]

    if len(valid_faces) == 0:
        raise HTTPException(
            status_code=400,
            detail="No sufficiently clear face detected. Try another photo.",
        )

    if len(valid_faces) > 1:
        raise HTTPException(
            status_code=400,
            detail="Multiple faces detected. Upload a photo showing only you.",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

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
        db.flush()

        save_student_embedding(
            db=db,
            student_id=student.id,
            image=image,
        )

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
    current_user=Depends(require_roles("STUDENT")),
):
    student = (
        db.query(Student)
        .filter(Student.user_id == current_user.id)
        .first()
    )

    if student is None:
        raise HTTPException(status_code=404, detail="Student profile not found")

    registration = (
        db.query(FaceRegistration)
        .filter(FaceRegistration.student_id == student.id)
        .first()
    )

    if registration is None:
        raise HTTPException(
            status_code=404,
            detail="Face registration not found",
        )

    return registration