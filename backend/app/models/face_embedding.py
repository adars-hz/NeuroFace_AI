from sqlalchemy import Column, Integer, String, ForeignKey, LargeBinary, DateTime, text
from app.database.connection import Base


class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(
        Integer,
        ForeignKey("students.id"),
        unique=True,
        nullable=False,
    )

    embedding = Column(LargeBinary, nullable=False)

    model_name = Column(
        String(50),
        nullable=False,
        default="facenet-vggface2",
    )

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )