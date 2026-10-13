
from pydantic import BaseModel, Field


class ClassroomCreate(BaseModel):
    class_name: str = Field(min_length=1, max_length=50)
    department_id: int = Field(gt=0)
    academic_year: str = Field(min_length=4, max_length=20)
    semester: int = Field(ge=1, le=8)


class ClassroomResponse(BaseModel):
    id: int
    class_name: str
    department_id: int
    academic_year: str
    semester: int

    model_config = {"from_attributes": True}
