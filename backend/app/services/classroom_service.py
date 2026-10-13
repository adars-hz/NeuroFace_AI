
from sqlalchemy.orm import Session

from app.models.classroom import Classroom
from app.schemas.classroom import ClassroomCreate


def create_classroom(db: Session, data: ClassroomCreate) -> Classroom:
    classroom = Classroom(
        class_name=data.class_name,
        department_id=data.department_id,
        academic_year=data.academic_year,
        semester=data.semester,
    )

    db.add(classroom)
    db.commit()
    db.refresh(classroom)

    return classroom
