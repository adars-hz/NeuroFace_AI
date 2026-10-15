
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    text,
)

from app.database.connection import Base


class FaceRegistration(Base):
    __tablename__ = "face_registrations"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(
        Integer,
        ForeignKey("students.id"),
        nullable=False,
        unique=True,
    )

    image_path = Column(String(500), nullable=False)

    status = Column(
        String(20),
        nullable=False,
        default="PENDING",
        server_default=text("'PENDING'"),
    )

    registered_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
