from sqlalchemy import Column, Integer, String, ForeignKey
from app.database.connection import Base


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    employee_id = Column(String(30), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    designation = Column(String(30), default="TEACHER", nullable=False)