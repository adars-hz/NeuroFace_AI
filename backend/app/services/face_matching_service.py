
import numpy as np
from sqlalchemy.orm import Session

from app.models.face_embedding import FaceEmbedding
from app.models.face_registration import FaceRegistration
from app.services.face_recognition_service import cosine_similarity


def find_matching_student(
    db: Session,
    query_embedding: np.ndarray,
    threshold: float = 0.75,
) -> dict:
    """
    Match a face only against approved student registrations.

    The similarity threshold is provisional and must be validated
    using representative face images before real-world use.
    """

    if query_embedding.shape != (512,):
        raise ValueError("Query embedding must contain 512 values.")

    records = (
        db.query(FaceEmbedding)
        .join(
            FaceRegistration,
            FaceRegistration.student_id == FaceEmbedding.student_id,
        )
        .filter(FaceRegistration.status == "APPROVED")
        .all()
    )

    if not records:
        return {
            "matched": False,
            "student_id": None,
            "similarity": None,
            "message": "No approved face registrations are available.",
        }

    best_student_id = None
    best_similarity = -1.0

    for record in records:
        stored_embedding = np.frombuffer(
            record.embedding,
            dtype=np.float32,
        )

        if stored_embedding.shape != (512,):
            continue

        similarity = cosine_similarity(
            query_embedding,
            stored_embedding,
        )

        if similarity > best_similarity:
            best_similarity = similarity
            best_student_id = record.student_id

    if best_student_id is not None and best_similarity >= threshold:
        return {
            "matched": True,
            "student_id": best_student_id,
            "similarity": float(best_similarity),
            "message": "Potential student match found.",
        }

    return {
        "matched": False,
        "student_id": None,
        "similarity": (
            float(best_similarity) if best_student_id is not None else None
        ),
        "message": "Unknown face. No sufficiently close match found.",
    }
