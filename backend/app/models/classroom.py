
from sqlalchemy import Column, Integer, String, ForeignKey
from app.database.connection import Base


class Classroom(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    class_name = Column(String(50), unique=True, nullable=False)
    department_id = Column(
        Integer,
        ForeignKey("departments.id"),
        nullable=False,
    )
    academic_year = Column(String(20), nullable=False)
    semester = Column(Integer, nullable=False)
