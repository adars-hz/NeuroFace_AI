
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    CheckConstraint,
    text,
)
from app.database.connection import Base


class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"

    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'CLOSED', 'EXPIRED')",
            name="ck_attendance_sessions_status",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    assignment_id = Column(
        Integer,
        ForeignKey("teacher_assignments.id"),
        nullable=False,
    )

    started_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    expires_at = Column(DateTime, nullable=False)

    ended_at = Column(DateTime, nullable=True)

    status = Column(
        String(20),
        nullable=False,
        default="ACTIVE",
        server_default=text("'ACTIVE'"),
    )
