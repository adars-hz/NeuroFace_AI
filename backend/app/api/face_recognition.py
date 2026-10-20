from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.database.deps import get_db
from app.services.face_recognition_service import generate_embedding
from app.services.face_matching_service import find_matching_student

router = APIRouter(
    prefix="/face-recognition",
    tags=["Face Recognition"],
)

MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


@router.post("/identify")
async def identify_face(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "TEACHER")),
):
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

        image = Image.open(BytesIO(content)).convert("RGB")

    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid image.")

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