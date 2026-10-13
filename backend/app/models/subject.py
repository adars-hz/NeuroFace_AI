
from sqlalchemy import Column, Integer, String, ForeignKey
from app.database.connection import Base


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    subject_code = Column(String(20), unique=True, nullable=False, index=True)
    subject_name = Column(String(100), nullable=False)
    class_id = Column(
        Integer,
        ForeignKey("classes.id"),
        nullable=False,
    )
