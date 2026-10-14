
from pydantic import BaseModel, Field


class TeacherAssignmentCreate(BaseModel):
    teacher_id: int = Field(gt=0)
    subject_id: int = Field(gt=0)
    class_id: int = Field(gt=0)


class TeacherAssignmentResponse(BaseModel):
    id: int
    teacher_id: int
    subject_id: int
    class_id: int

    model_config = {"from_attributes": True}
