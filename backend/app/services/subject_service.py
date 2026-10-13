
from sqlalchemy.orm import Session

from app.models.subject import Subject
from app.schemas.subject import SubjectCreate


def create_subject(db: Session, data: SubjectCreate) -> Subject:
    subject = Subject(
        subject_code=data.subject_code.strip().upper(),
        subject_name=data.subject_name.strip(),
        class_id=data.class_id,
    )

    db.add(subject)
    db.commit()
    db.refresh(subject)

    return subject
