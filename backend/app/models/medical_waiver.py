
from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    ForeignKey,
    Text,
    CheckConstraint,
    text,
)
from app.database.connection import Base


class MedicalWaiver(Base):
    __tablename__ = "medical_waivers"

    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'REJECTED')",
            name="ck_medical_waiver_status",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(
        Integer, ForeignKey("students.id"), nullable=False, index=True
    )
    subject_id = Column(
        Integer, ForeignKey("subjects.id"), nullable=False, index=True
    )
    approved_by = Column(
        Integer, ForeignKey("users.id"), nullable=False
    )

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    certificate_path = Column(String(500), nullable=False)
    reason = Column(Text, nullable=True)

    status = Column(
        String(20),
        nullable=False,
        default="PENDING",
        server_default=text("'PENDING'"),
    )

    reviewed_at = Column(DateTime, nullable=True)
    review_comment = Column(Text, nullable=True)

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
