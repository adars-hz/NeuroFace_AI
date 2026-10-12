from sqlalchemy import Column, Integer, String, ForeignKey
from app.database.connection import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    student_id = Column(String(30), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    class_name = Column(String(50), nullable=False)
    face_registered = Column(String(10), default="NO", nullable=False)