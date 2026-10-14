
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    text,
)

from app.database.connection import Base


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "student_id",
            name="uq_attendance_session_student",
        ),
        CheckConstraint(
            "status IN ('PRESENT', 'ABSENT', 'LEAVE')",
            name="ck_attendance_record_status",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    session_id = Column(
        Integer,
        ForeignKey("attendance_sessions.id"),
        nullable=False,
    )

    student_id = Column(
        Integer,
        ForeignKey("students.id"),
        nullable=False,
    )

    status = Column(
        String(20),
        nullable=False,
        default="PRESENT",
        server_default=text("'PRESENT'"),
    )

    marked_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    marked_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )
