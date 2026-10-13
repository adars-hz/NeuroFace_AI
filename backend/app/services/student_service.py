
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.models.student import Student
from app.schemas.student import StudentCreate


def create_student(db: Session, data: StudentCreate) -> Student:
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        role="STUDENT",
    )

    db.add(user)
    db.flush()

    student = Student(
        user_id=user.id,
        student_id=data.student_id,
        full_name=data.full_name,
        class_name=data.class_name,
        face_registered="NO",
    )

    db.add(student)
    db.commit()
    db.refresh(student)

    return student
