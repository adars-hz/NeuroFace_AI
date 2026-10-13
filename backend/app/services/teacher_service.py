
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.models.teacher import Teacher
from app.schemas.teacher import TeacherCreate


def create_teacher(db: Session, data: TeacherCreate) -> Teacher:
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        role="TEACHER",
    )

    db.add(user)
    db.flush()

    teacher = Teacher(
        user_id=user.id,
        employee_id=data.employee_id,
        full_name=data.full_name,
        designation=data.designation,
    )

    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    return teacher
