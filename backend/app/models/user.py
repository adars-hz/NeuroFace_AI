
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    CheckConstraint,
    text,
)

from app.database.connection import Base


class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint(
            "role IN ('ADMIN', 'TEACHER', 'STUDENT')",
            name="ck_users_valid_role",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash = Column(
        String(255),
        nullable=False,
    )

    role = Column(
        String(20),
        nullable=False,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),
    )