import numpy as np
from PIL import Image
from sqlalchemy.orm import Session

from app.models.face_embedding import FaceEmbedding
from app.services.face_recognition_service import generate_embedding


def save_student_embedding(
    db: Session,
    student_id: int,
    image: Image.Image,
) -> FaceEmbedding:
    """Generate and store one student's face embedding."""

    vector = generate_embedding(image)

    existing = (
        db.query(FaceEmbedding)
        .filter(FaceEmbedding.student_id == student_id)
        .first()
    )

    embedding_bytes = vector.astype(np.float32).tobytes()

    if existing:
        existing.embedding = embedding_bytes
        existing.model_name = "facenet-vggface2"
        db.commit()
        db.refresh(existing)
        return existing

    record = FaceEmbedding(
        student_id=student_id,
        embedding=embedding_bytes,
        model_name="facenet-vggface2",
    )

    try:
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    except Exception:
        db.rollback()
        raise


def load_student_embedding(
    db: Session,
    student_id: int,
) -> np.ndarray | None:
    """Load a student's stored 512-dimensional vector."""

    record = (
        db.query(FaceEmbedding)
        .filter(FaceEmbedding.student_id == student_id)
        .first()
    )

    if record is None:
        return None

    vector = np.frombuffer(record.embedding, dtype=np.float32)

    if vector.shape != (512,):
        raise ValueError("Stored face embedding has an invalid size.")

    return vector.copy()