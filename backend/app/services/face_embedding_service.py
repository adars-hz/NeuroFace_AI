
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
    """Generate and store one student's 512-dimensional face embedding."""

    vector = generate_embedding(image)

    if vector.shape != (512,):
        raise ValueError("Generated face embedding must contain 512 values.")

    embedding_bytes = vector.astype(np.float32).tobytes()

    record = (
        db.query(FaceEmbedding)
        .filter(FaceEmbedding.student_id == student_id)
        .first()
    )

    if record is None:
        record = FaceEmbedding(
            student_id=student_id,
            embedding=embedding_bytes,
            model_name="facenet-vggface2",
        )
        db.add(record)
    else:
        record.embedding = embedding_bytes
        record.model_name = "facenet-vggface2"

    return record


def load_student_embedding(
    db: Session,
    student_id: int,
) -> np.ndarray | None:
    """Load a student's stored 512-dimensional face embedding."""

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
