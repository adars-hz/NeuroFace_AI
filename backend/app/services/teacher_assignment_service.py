
from sqlalchemy.orm import Session

from app.models.teacher_assignment import TeacherAssignment
from app.schemas.teacher_assignment import TeacherAssignmentCreate


def create_assignment(
    db: Session,
    data: TeacherAssignmentCreate,
) -> TeacherAssignment:
    assignment = TeacherAssignment(
        teacher_id=data.teacher_id,
        subject_id=data.subject_id,
        class_id=data.class_id,
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return assignment
