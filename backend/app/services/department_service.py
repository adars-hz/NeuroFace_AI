
from sqlalchemy.orm import Session

from app.models.department import Department
from app.schemas.department import DepartmentCreate


def create_department(db: Session, data: DepartmentCreate) -> Department:
    department = Department(
        department_code=data.department_code.strip().upper(),
        department_name=data.department_name.strip(),
    )

    db.add(department)
    db.commit()
    db.refresh(department)

    return department
